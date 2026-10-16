# PathruleBench v3 results: python

Trials 1, 2, 3. Mean passes over trials [min–max] / probes. `memory` = probes of knowledge stated in an earlier session or seeded; `present` = seeded team knowledge; `told` = what the session's own prompts asked (harm control).

| Arm | n | memory | present | told | Cost USD | Steps |
| --- | --- | --- | --- | --- | --- | --- |
| none | 3 | 4.7 [4–6] / 26 | 8.0 [8–8] / 8 | 19.0 [19–19] / 19 | 1.30 | 199 |
| claude_md | 3 | 22.3 [21–24] / 26 | 8.0 [8–8] / 8 | 19.0 [19–19] / 19 | 2.06 | 154 |
| pathrule | 3 | 25.0 [24–26] / 26 | 8.0 [8–8] / 8 | 19.0 [19–19] / 19 | 1.70 | 161 |

## Memory probes by category (mean passes / probes)

| Arm | abstention | adjacent | decision | habit | lesson | stale | superseded |
| --- | --- | --- | --- | --- | --- | --- | --- |
| none | 1.0 [0–2] / 2 | 1.0 [1–1] / 1 | 0.0 [0–0] / 10 | 0.7 [0–1] / 7 | 0.0 [0–0] / 1 | 2.0 [2–2] / 2 | 0.0 [0–0] / 3 |
| claude_md | 2.0 [2–2] / 2 | 1.0 [1–1] / 1 | 9.7 [9–10] / 10 | 6.3 [6–7] / 7 | 0.0 [0–0] / 1 | 1.3 [0–2] / 2 | 2.0 [0–3] / 3 |
| pathrule | 2.0 [2–2] / 2 | 1.0 [1–1] / 1 | 9.7 [9–10] / 10 | 6.7 [6–7] / 7 | 0.7 [0–1] / 1 | 2.0 [2–2] / 2 | 3.0 [3–3] / 3 |

## Paired differences (pathrule minus claude_md), bootstrap 95% CI over probes

- memory: +0.10 [+0.03, +0.19] over 26 probes
- present: +0.00 [+0.00, +0.00] over 8 probes
- told: +0.00 [+0.00, +0.00] over 19 probes

## Probes every arm failed or passed in every trial

| Probe | category | none | claude_md | pathrule |
| --- | --- | --- | --- | --- |
| s1_added_headers_retry_after | told | 1.00 | 1.00 | 1.00 |
| s1_deadline_504 | told | 1.00 | 1.00 | 1.00 |
| s1_deadline_problem_format | present | 1.00 | 1.00 | 1.00 |
| s1_docstrings | told | 1.00 | 1.00 | 1.00 |
| s1_option_registered | present | 1.00 | 1.00 | 1.00 |
| s1_retry_after | told | 1.00 | 1.00 | 1.00 |
| s2_docstrings | told | 1.00 | 1.00 | 1.00 |
| s2_internal_exempt | told | 1.00 | 1.00 | 1.00 |
| s2_option_registered | present | 1.00 | 1.00 | 1.00 |
| s2_query_keys_400 | told | 1.00 | 1.00 | 1.00 |
| s2_spdx | told | 1.00 | 1.00 | 1.00 |
| s3_404_problem | told | 1.00 | 1.00 | 1.00 |
| s3_default_header_limit | told | 1.00 | 1.00 | 1.00 |
| s3_docstrings_untold | habit | 0.00 | 1.00 | 1.00 |
| s3_spdx_untold | decision | 0.00 | 1.00 | 1.00 |
| s4_added_headers_deprecation | decision | 0.00 | 1.00 | 1.00 |
| s4_deprecation_header | told | 1.00 | 1.00 | 1.00 |
| s4_docstrings_untold | habit | 0.00 | 1.00 | 1.00 |
| s4_gone_410 | told | 1.00 | 1.00 | 1.00 |
| s4_gone_new_domain | superseded | 0.00 | 0.67 | 1.00 |
| s4_limit_new_path | stale | 1.00 | 0.67 | 1.00 |
| s4_route_option_registered | present | 1.00 | 1.00 | 1.00 |
| s4_spdx_untold | decision | 0.00 | 1.00 | 1.00 |
| s5_429_new_domain | superseded | 0.00 | 0.67 | 1.00 |
| s5_429_problem | told | 1.00 | 1.00 | 1.00 |
| s5_abstains_on_undecided_limits | abstention | 0.33 | 1.00 | 1.00 |
| s5_added_headers_ratelimit | decision | 0.00 | 1.00 | 1.00 |
| s5_docs_rate_limit | told | 1.00 | 1.00 | 1.00 |
| s5_docstrings_untold | habit | 0.00 | 1.00 | 1.00 |
| s5_route_option_registered | present | 1.00 | 1.00 | 1.00 |
| s5_spdx_untold | decision | 0.00 | 1.00 | 1.00 |
| s6_cli_plain_error | adjacent | 1.00 | 1.00 | 1.00 |
| s6_docstrings_untold | habit | 0.00 | 0.67 | 1.00 |
| s6_option_registered | present | 1.00 | 1.00 | 1.00 |
| s6_slow_warning | told | 1.00 | 1.00 | 1.00 |
| s6_spdx_untold | decision | 0.00 | 1.00 | 1.00 |
| s7_413_new_domain | superseded | 0.00 | 0.67 | 1.00 |
| s7_added_headers_request_id | decision | 0.00 | 1.00 | 1.00 |
| s7_changelog | told | 1.00 | 1.00 | 1.00 |
| s7_docstrings_untold | habit | 0.00 | 1.00 | 1.00 |
| s7_max_body_413 | told | 1.00 | 1.00 | 1.00 |
| s7_option_registered | present | 1.00 | 1.00 | 1.00 |
| s7_request_id | told | 1.00 | 1.00 | 1.00 |
| s7_spdx_untold | decision | 0.00 | 1.00 | 1.00 |
| s8_abstains_on_undecided_limits | abstention | 0.67 | 1.00 | 1.00 |
| s8_added_headers_cors | decision | 0.00 | 0.67 | 0.67 |
| s8_changelog_untold | habit | 0.67 | 1.00 | 0.67 |
| s8_cors_header | told | 1.00 | 1.00 | 1.00 |
| s8_docstrings_untold | habit | 0.00 | 0.67 | 1.00 |
| s8_limit_new_path_untold | stale | 1.00 | 0.67 | 1.00 |
| s8_option_registered | present | 1.00 | 1.00 | 1.00 |
| s8_spdx_untold | decision | 0.00 | 1.00 | 1.00 |
| s8_suite_lesson_kept | lesson | 0.00 | 0.00 | 0.67 |
