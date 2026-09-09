#!/usr/bin/env Rscript
# Temporary exact-source materializer for FFBK/NextGen research execution only.
# Mirrors the documented CASdatasets freclaimset2motor list-object contract.

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3L) {
  stop("usage: materialize_freclaimset2motor_exact.R SOURCE_RDA CLAIMS_CSV AGG_CSV")
}

source_rda <- args[[1L]]
claims_csv <- args[[2L]]
agg_csv <- args[[3L]]

if (!file.exists(source_rda)) {
  stop("source .rda does not exist")
}

env <- new.env(parent = baseenv())
loaded <- load(source_rda, envir = env)
expected_top_level <- "freclaimset2motor"
if (!identical(sort(loaded), expected_top_level)) {
  stop(sprintf(
    "source .rda top-level objects mismatch: expected=%s observed=%s",
    expected_top_level,
    paste(sort(loaded), collapse = ",")
  ))
}

bundle <- get(expected_top_level, envir = env, inherits = FALSE)
if (!is.list(bundle)) {
  stop("freclaimset2motor must be a list")
}
required_components <- c("claimset", "aggdata")
if (!all(required_components %in% names(bundle))) {
  stop(sprintf(
    "freclaimset2motor missing required components: %s",
    paste(setdiff(required_components, names(bundle)), collapse = ",")
  ))
}

claimset <- bundle[["claimset"]]
aggdata <- bundle[["aggdata"]]
if (!is.data.frame(claimset) || !is.data.frame(aggdata)) {
  stop("freclaimset2motor$claimset and $aggdata must both be data.frames")
}

write.table(
  claimset, file = claims_csv, sep = ",", row.names = FALSE, col.names = TRUE,
  quote = TRUE, na = "NA", qmethod = "double", eol = "\n", fileEncoding = "UTF-8"
)
write.table(
  aggdata, file = agg_csv, sep = ",", row.names = FALSE, col.names = TRUE,
  quote = TRUE, na = "NA", qmethod = "double", eol = "\n", fileEncoding = "UTF-8"
)

cat(sprintf(
  "FRECLAIMSET2MOTOR_MATERIALIZE_OK top_level=%s components=%s claim_rows=%d agg_rows=%d\n",
  expected_top_level,
  paste(sort(required_components), collapse = ","),
  nrow(claimset),
  nrow(aggdata)
))
