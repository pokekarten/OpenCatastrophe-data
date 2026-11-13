# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic, offline exact RVO/PDOK BRP OGC collection tests."""
from __future__ import annotations
import copy
from datetime import datetime,timezone
import hashlib
import json
import unittest
from unittest.mock import patch
from scripts.probe_pdok_brp_2025_collection_v0 import (
 ACCESS_ID,SOURCE_ID,BASE,COLLECTION_PATH,URL,TIMEOUT,MAX_BYTES,CRS84,EPSG28992,
 BRPBlocked,NoRedirect,inspect_collection,verify_reviewed_contract,probe,main,
)
from scripts.validate_source_access import validate_path
from pathlib import Path

def fixture():
 return {"id":"brpgewas","title":"BRP Gewaspercelen",
  "description":"Landbouwpercelen en gewas per RVO BRP verklaring 15 mei",
  "itemType":"feature","crs":[CRS84,EPSG28992],
  "storageCrs":EPSG28992,
  "extent":{"spatial":{"crs":CRS84,"bbox":[[-1.65,48.04,12.43,56.11]]}},
  "links":[{"rel":"self","href":URL,"type":"application/json"},
    {"rel":"items","href":"https://api.pdok.nl/never/follow"}],
  "updated":"2026-05-15T08:11:40Z"}

def encoded(x):
 return json.dumps(x,ensure_ascii=False,sort_keys=True).encode("utf-8")

class FakeResponse:
 def __init__(self,raw=None,status=200,url=URL,media="application/json",headers=None):
  self.raw=encoded(fixture()) if raw is None else raw
  self.status=status
  self.url=url
  self.headers={"Content-Type":media,"Content-Encoding":"identity","Content-Length":str(len(self.raw))}
  self.headers.update(headers or {})
 def geturl(self): return self.url
 def read(self,n): return self.raw[:n]
 def __enter__(self):return self
 def __exit__(self,*args):return False

class BRPCollectionGateTests(unittest.TestCase):
 def test_exact_reviewed_metadata_contract(self):
  verify_reviewed_contract()
  self.assertEqual(ACCESS_ID,"nl.rvo.brp-gewaspercelen.2025.ogc-collection")
  self.assertEqual(SOURCE_ID,"nl.rvo.brp-gewaspercelen.2025")
  self.assertEqual(URL,BASE+COLLECTION_PATH+"?f=json")

 def test_correct_synthetic_response_is_not_parcel_sample(self):
  v=inspect_collection(encoded(fixture()))
  self.assertTrue(v["bbox_overlaps_netherlands_verified"])
  self.assertEqual(v["original_feature_requests"],0)
  self.assertFalse(v["original_parcel_geometry_downloaded"])
  self.assertFalse(v["frozen_2025_vintage_proven"])
  self.assertFalse(v["model_input_approved"])

 def test_wrong_source_crs_bbox_or_self_link_rejected(self):
  for key,value in (("id","other"),("title","Other"),("itemType","FeatureCollection"),("storageCrs",CRS84)):
   with self.subTest(key=key):
    x=fixture(); x[key]=value
    with self.assertRaises(BRPBlocked):inspect_collection(encoded(x))
  for kind in ("bbox","crs","self","description","double_self"):
   x=fixture()
   if kind=="bbox":x["extent"]["spatial"]["bbox"]=[[90.,40.,100.,45.]]
   elif kind=="crs":x["crs"]=[CRS84]
   elif kind=="self":x["links"][0]["href"]="https://api.pdok.nl/wrong"
   elif kind=="description":x["description"]="not agriculture"
   elif kind=="double_self":x["links"].append(copy.deepcopy(x["links"][0]))
   with self.subTest(kind=kind),self.assertRaises(BRPBlocked):inspect_collection(encoded(x))

 def test_invalid_original_json_rejected(self):
  for raw in (b"",b"[]",b"not-json",b'{"a":1,"a":2}',b'{"a":NaN}',b'\xff',b"x"*(MAX_BYTES+1)):
   with self.subTest(raw=raw[:20]),self.assertRaises(BRPBlocked):inspect_collection(raw)

 def test_one_exact_get_and_sha_receipt(self):
  hits=[]
  def fake_open(req,timeout):
   hits.append((req.full_url,req.get_method(),timeout))
   return FakeResponse()
  receipt=probe(open_request=fake_open,clock=lambda:datetime(2026,11,13,tzinfo=timezone.utc))
  self.assertEqual(hits,[(URL,"GET",TIMEOUT)])
  self.assertEqual(receipt["response_sha256"],hashlib.sha256(encoded(fixture())).hexdigest())
  self.assertEqual(receipt["original_feature_requests"],0)
  self.assertFalse(receipt["original_response_body_persisted"])
  self.assertFalse(receipt["model_input_admitted"])
  self.assertNotIn("links",receipt)

 def test_http_response_status_redirect_content_and_length_fail(self):
  bads=[FakeResponse(status=206),FakeResponse(url="https://other.invalid"),
   FakeResponse(media="text/html"),FakeResponse(headers={"Content-Encoding":"gzip"}),
   FakeResponse(headers={"Content-Length":"NaN"}),
   FakeResponse(headers={"Content-Length":str(MAX_BYTES+1)}),
   FakeResponse(headers={"Content-Length":"1"}),
   FakeResponse(raw=b"x"*(MAX_BYTES+1))]
  for r in bads:
   with self.subTest(status=r.status,headers=r.headers),self.assertRaises(BRPBlocked):
    probe(open_request=lambda req,timeout:r)

 def test_manual_only_no_automatic_network(self):
  with patch("scripts.probe_pdok_brp_2025_collection_v0.probe") as p:
   with self.assertRaises(SystemExit) as e:main([])
   p.assert_not_called()
   self.assertEqual(e.exception.code,2)

 def test_source_terms_revoked_blocks_live_preflight(self):
  from scripts.probe_pdok_brp_2025_collection_v0 import CONTRACT_PATH
  obj=copy.deepcopy(validate_path(CONTRACT_PATH))
  obj["rights_and_policy"]["commercial_automation_status"]="unknown"
  with patch("scripts.probe_pdok_brp_2025_collection_v0.validate_path",return_value=obj):
   with self.assertRaises(BRPBlocked):verify_reviewed_contract()

 def test_redirect_not_followed(self):
  with self.assertRaises(BRPBlocked):
   NoRedirect().redirect_request(None,None,302,"moved",{},"https://other.invalid")

if __name__ == "__main__":
 unittest.main()
