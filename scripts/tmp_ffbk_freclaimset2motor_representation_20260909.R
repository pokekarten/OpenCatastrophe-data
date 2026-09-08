args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) stop("usage: Rscript runner.R <source.rda> <outdir>")
source_path <- args[[1]]
outdir <- args[[2]]
dir.create(outdir, recursive = TRUE, showWarnings = FALSE)

load(source_path)
if (!exists("freclaimset2motor")) stop("freclaimset2motor object missing")
if (!is.list(freclaimset2motor) || !all(c("claimset", "aggdata") %in% names(freclaimset2motor))) stop("unexpected top-level object")
d0 <- freclaimset2motor$claimset
agg <- freclaimset2motor$aggdata
required <- c("ClaimID", "OccurYear", "ManagYear", "ClaimStatus", "PaidAmount", "RecourseAmount", "ExpectCharge", "ExpectRecourse")
if (!all(required %in% names(d0))) stop("required claim fields missing")

rows_raw <- nrow(d0)
exact_dup <- duplicated(d0)
exact_dup_n <- sum(exact_dup)
d <- d0[!exact_dup, , drop = FALSE]
key <- paste(d$ClaimID, d$ManagYear, sep = "|")
dup_key <- duplicated(key) | duplicated(key, fromLast = TRUE)
bad_claims <- unique(as.character(d$ClaimID[dup_key]))
bad_claim_n <- length(bad_claims)
d <- d[!(as.character(d$ClaimID) %in% bad_claims), , drop = FALSE]
ord <- order(as.character(d$ClaimID), as.integer(d$ManagYear), method = "radix")
d <- d[ord, , drop = FALSE]
rownames(d) <- NULL

id <- as.character(d$ClaimID)
yr <- as.integer(d$ManagYear)
occ <- as.integer(d$OccurYear)
status <- tolower(trimws(as.character(d$ClaimStatus)))
praw <- as.numeric(d$PaidAmount)
if (any(!is.finite(praw))) stop("non-finite PaidAmount")
neg_cumulative_n <- sum(praw < 0)
if (neg_cumulative_n > 0) stop(sprintf("negative cumulative PaidAmount states: %d", neg_cumulative_n))

status_levels <- sort(unique(status))
closed_label <- "fully closed"
if (!(closed_label %in% status_levels)) stop(sprintf("expected status '%s' absent; observed: %s", closed_label, paste(status_levels, collapse = ", ")))
is_closed <- status == closed_label

n <- nrow(d)
pmono <- numeric(n)
pabsorb <- numeric(n)
running_max <- -Inf
closed_seen <- FALSE
freeze_paid <- NA_real_
for (j in seq_len(n)) {
  new_claim <- (j == 1L) || (id[[j]] != id[[j - 1L]])
  if (new_claim) {
    running_max <- -Inf
    closed_seen <- FALSE
    freeze_paid <- NA_real_
  }
  running_max <- max(running_max, praw[[j]])
  pmono[[j]] <- running_max
  if (!closed_seen && is_closed[[j]]) {
    closed_seen <- TRUE
    freeze_paid <- praw[[j]]
  }
  pabsorb[[j]] <- if (closed_seen) freeze_paid else praw[[j]]
}

# Frozen contract calibration: latest state available at or before management year 2004.
cal_idx_all <- which(yr <= 2004L)
if (length(cal_idx_all) == 0L) stop("no calibration states <= 2004")
cal_id <- id[cal_idx_all]
cal_last <- !duplicated(cal_id, fromLast = TRUE)
cal_idx <- cal_idx_all[cal_last]
cal_paid <- praw[cal_idx]
cal_total <- sum(cal_paid)
if (!(cal_total > 0)) stop("non-positive calibration paid total")
target_ceded <- 0.30 * cal_total
f_attach <- function(a) sum(pmax(cal_paid - a, 0)) - target_ceded
upper <- max(cal_paid)
if (f_attach(0) < 0 || f_attach(upper) > 0) stop("attachment root not bracketed")
attachment <- uniroot(f_attach, lower = 0, upper = upper, tol = 1e-10)$root
cal_xol_ceded <- sum(pmax(cal_paid - attachment, 0))
cal_match_rel_error <- abs(cal_xol_ceded - target_ceded) / target_ceded

# Explicit consecutive annual observation pairs only.
base <- seq_len(n - 1L)
same_claim <- id[base] == id[base + 1L]
consecutive <- yr[base + 1L] == yr[base] + 1L
eval_year <- yr[base] >= 2005L & yr[base] <= 2013L
idx <- base[same_claim & consecutive & eval_year]
if (length(idx) < 1000L) stop("too few evaluation transitions")
nxt <- idx + 1L

# Source diagnostics on the retained unambiguous primary population.
all_pair <- base[same_claim & consecutive]
all_nxt <- all_pair + 1L
raw_negative_transition_n <- sum((praw[all_nxt] - praw[all_pair]) < 0)
raw_negative_transition_eur <- sum((praw[all_nxt] - praw[all_pair])[praw[all_nxt] - praw[all_pair] < 0])
closed_to_not_closed_n <- sum(is_closed[all_pair] & !is_closed[all_nxt])

tail_stats <- function(x) {
  x <- x[is.finite(x)]
  if (length(x) == 0L) stop("empty tail input")
  sx <- sort(x, decreasing = TRUE)
  q99 <- as.numeric(quantile(x, 0.99, type = 1, names = FALSE))
  q995 <- as.numeric(quantile(x, 0.995, type = 1, names = FALSE))
  k <- max(1L, ceiling(0.005 * length(x)))
  es995 <- mean(sx[seq_len(k)])
  c(VaR99 = q99, VaR995 = q995, ES995 = es995)
}

rep_paths <- list(raw_signed = praw, monotone_cleaned = pmono, absorbing_settlement = pabsorb)
programme_names <- c("QS30", "XOL")
metric_rows <- list()
year_rows <- list()
transition_rows <- list()

for (rep_name in names(rep_paths)) {
  p <- rep_paths[[rep_name]]
  gross <- p[nxt] - p[idx]
  for (prog in programme_names) {
    cum_ceded <- if (prog == "QS30") 0.30 * p else pmax(p - attachment, 0)
    ceded <- cum_ceded[nxt] - cum_ceded[idx]
    retained <- gross - ceded
    ts <- tail_stats(retained)
    metric_rows[[length(metric_rows) + 1L]] <- data.frame(
      representation = rep_name,
      programme = prog,
      transitions = length(idx),
      gross_total = sum(gross),
      gross_positive_total = sum(pmax(gross, 0)),
      gross_negative_total = sum(pmin(gross, 0)),
      ceded_total = sum(ceded),
      retained_total = sum(retained),
      VaR99 = ts[["VaR99"]],
      VaR995 = ts[["VaR995"]],
      ES995 = ts[["ES995"]],
      stringsAsFactors = FALSE
    )
    ys <- sort(unique(yr[idx]))
    for (yy in ys) {
      z <- yr[idx] == yy
      tsy <- tail_stats(retained[z])
      year_rows[[length(year_rows) + 1L]] <- data.frame(
        representation = rep_name,
        programme = prog,
        management_year = yy,
        transitions = sum(z),
        gross_total = sum(gross[z]),
        ceded_total = sum(ceded[z]),
        retained_total = sum(retained[z]),
        VaR995 = tsy[["VaR995"]],
        ES995 = tsy[["ES995"]],
        stringsAsFactors = FALSE
      )
    }
    transition_rows[[paste(rep_name, prog, sep = "|")]] <- data.frame(
      ClaimID = id[idx], ManagYear = yr[idx], gross = gross, ceded = ceded, retained = retained,
      stringsAsFactors = FALSE
    )
  }
}
metrics <- do.call(rbind, metric_rows)
year_metrics <- do.call(rbind, year_rows)

raw_gross_positive <- metrics$gross_positive_total[metrics$representation == "raw_signed" & metrics$programme == "QS30"][[1]]
raw_qs <- transition_rows[["raw_signed|QS30"]]
raw_xol <- transition_rows[["raw_signed|XOL"]]

screen_rows <- list()
for (rep_name in c("monotone_cleaned", "absorbing_settlement")) {
  for (prog in programme_names) {
    rawm <- metrics[metrics$representation == "raw_signed" & metrics$programme == prog, , drop = FALSE]
    repm <- metrics[metrics$representation == rep_name & metrics$programme == prog, , drop = FALSE]
    rawt <- transition_rows[[paste("raw_signed", prog, sep = "|")]]
    rept <- transition_rows[[paste(rep_name, prog, sep = "|")]]
    ceded_diff <- rept$ceded - rawt$ceded
    retained_diff <- rept$retained - rawt$retained
    rel_var995 <- if (abs(rawm$VaR995) > 0) abs(repm$VaR995 - rawm$VaR995) / abs(rawm$VaR995) else NA_real_
    rel_es995 <- if (abs(rawm$ES995) > 0) abs(repm$ES995 - rawm$ES995) / abs(rawm$ES995) else NA_real_
    cession_screen_ratio <- abs(sum(ceded_diff)) / raw_gross_positive
    screen_rows[[length(screen_rows) + 1L]] <- data.frame(
      representation = rep_name,
      programme = prog,
      changed_ceded_transitions = sum(abs(ceded_diff) > 1e-9),
      sum_abs_ceded_transition_diff = sum(abs(ceded_diff)),
      cumulative_ceded_diff_vs_raw = sum(ceded_diff),
      cumulative_retained_diff_vs_raw = sum(retained_diff),
      cession_screen_ratio = cession_screen_ratio,
      rel_change_VaR995 = rel_var995,
      rel_change_ES995 = rel_es995,
      cession_screen_crossed = cession_screen_ratio > 0.005,
      tail_screen_crossed = (is.finite(rel_var995) && rel_var995 > 0.01) || (is.finite(rel_es995) && rel_es995 > 0.01),
      stringsAsFactors = FALSE
    )
  }
}
screens <- do.call(rbind, screen_rows)

winner <- function(rep_name, metric) {
  m <- metrics[metrics$representation == rep_name, , drop = FALSE]
  a <- m[m$programme == "QS30", metric][[1]]
  b <- m[m$programme == "XOL", metric][[1]]
  if (abs(a - b) <= 1e-12) "TIE" else if (a < b) "QS30" else "XOL"
}
winners <- data.frame(
  representation = names(rep_paths),
  VaR995_winner = vapply(names(rep_paths), winner, character(1), metric = "VaR995"),
  ES995_winner = vapply(names(rep_paths), winner, character(1), metric = "ES995"),
  stringsAsFactors = FALSE
)
raw_var_winner <- winners$VaR995_winner[winners$representation == "raw_signed"][[1]]
raw_es_winner <- winners$ES995_winner[winners$representation == "raw_signed"][[1]]
winners$VaR995_flip_vs_raw <- winners$VaR995_winner != raw_var_winner
winners$ES995_flip_vs_raw <- winners$ES995_winner != raw_es_winner

# Concentration of representation changes around the XoL attachment.
near_attach <- abs(praw[idx] - attachment) <= 0.10 * max(attachment, 1) | abs(praw[nxt] - attachment) <= 0.10 * max(attachment, 1)
raw_to_mono_xol <- transition_rows[["monotone_cleaned|XOL"]]$ceded - transition_rows[["raw_signed|XOL"]]$ceded
raw_to_abs_xol <- transition_rows[["absorbing_settlement|XOL"]]$ceded - transition_rows[["raw_signed|XOL"]]$ceded
concentration <- data.frame(
  comparison = c("monotone_vs_raw_XOL", "absorbing_vs_raw_XOL"),
  changed_transitions = c(sum(abs(raw_to_mono_xol) > 1e-9), sum(abs(raw_to_abs_xol) > 1e-9)),
  changed_near_attachment = c(sum(abs(raw_to_mono_xol) > 1e-9 & near_attach), sum(abs(raw_to_abs_xol) > 1e-9 & near_attach)),
  abs_ceded_diff_near_attachment = c(sum(abs(raw_to_mono_xol[near_attach])), sum(abs(raw_to_abs_xol[near_attach]))),
  abs_ceded_diff_total = c(sum(abs(raw_to_mono_xol)), sum(abs(raw_to_abs_xol))),
  stringsAsFactors = FALSE
)
concentration$near_attachment_share_abs_diff <- ifelse(concentration$abs_ceded_diff_total > 0, concentration$abs_ceded_diff_near_attachment / concentration$abs_ceded_diff_total, NA_real_)

write.csv(metrics, file.path(outdir, "metrics.csv"), row.names = FALSE)
write.csv(year_metrics, file.path(outdir, "year_metrics.csv"), row.names = FALSE)
write.csv(screens, file.path(outdir, "screens.csv"), row.names = FALSE)
write.csv(winners, file.path(outdir, "winners.csv"), row.names = FALSE)
write.csv(concentration, file.path(outdir, "concentration.csv"), row.names = FALSE)

cat("RESEARCH_RECEIPT_BEGIN\n")
cat(sprintf("rows_raw=%d\n", rows_raw))
cat(sprintf("exact_duplicate_rows_removed=%d\n", exact_dup_n))
cat(sprintf("bad_claims_excluded_for_conflicting_claim_year=%d\n", bad_claim_n))
cat(sprintf("rows_primary=%d\n", nrow(d)))
cat(sprintf("status_levels=%s\n", paste(status_levels, collapse = ";")))
cat(sprintf("negative_cumulative_paid_states=%d\n", neg_cumulative_n))
cat(sprintf("calibration_states_asof_2004=%d\n", length(cal_idx)))
cat(sprintf("calibration_paid_total=%.10f\n", cal_total))
cat(sprintf("xol_attachment=%.10f\n", attachment))
cat(sprintf("xol_calibration_match_rel_error=%.12g\n", cal_match_rel_error))
cat(sprintf("evaluation_transitions=%d\n", length(idx)))
cat(sprintf("retained_population_negative_paid_transitions=%d\n", raw_negative_transition_n))
cat(sprintf("retained_population_negative_paid_eur=%.10f\n", raw_negative_transition_eur))
cat(sprintf("retained_population_closed_to_not_closed=%d\n", closed_to_not_closed_n))
cat("\nPRIMARY_METRICS\n")
print(metrics, row.names = FALSE, digits = 12)
cat("\nSCREENS\n")
print(screens, row.names = FALSE, digits = 12)
cat("\nWINNERS\n")
print(winners, row.names = FALSE)
cat("\nCONCENTRATION\n")
print(concentration, row.names = FALSE, digits = 12)
cat("\nYEAR_METRICS\n")
print(year_metrics, row.names = FALSE, digits = 12)
cat("RESEARCH_RECEIPT_END\n")
