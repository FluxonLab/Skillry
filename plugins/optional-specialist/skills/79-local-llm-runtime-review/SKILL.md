---
name: local-llm-runtime-review
description: Use when you need to review local LLM runtimes, model routing, resource limits, privacy boundaries, and offline behavior.
---

# Local LLM Runtime Review

## Purpose

Review a local LLM runtime setup — Ollama, llama.cpp, LM Studio, vLLM, or similar — for model selection, quantization correctness, VRAM/RAM fit, context length configuration, throughput characteristics, model routing logic, and privacy boundary enforcement. Produces concrete configuration recommendations with expected performance impact — not generic "optimize your hardware" advice.

## When to use

- A local LLM runtime is being set up for the first time and needs a configuration review before use with any real data.
- Inference is slower than expected and the bottleneck is unclear — VRAM overflow, RAM bandwidth, CPU offload, or quantization level.
- A model is being selected for local deployment and you need to compare options against the available hardware.
- The runtime routes between local and cloud models and you need to verify the routing logic correctly enforces privacy boundaries.
- Privacy requirements mandate that certain data categories never leave the local machine and you need to confirm the runtime enforces this.
- A quantized model is producing degraded output quality and the quantization level may be the cause.
- The model weights are being updated and you need a review before the update is applied to a system processing sensitive data.

## When not to use

- The application uses only cloud-hosted LLM APIs — local runtime concerns do not apply.
- The question is about prompt quality or evaluation methodology, not runtime configuration.
- The infrastructure is a cloud GPU cluster managed by a platform team — this skill covers local/edge runtimes only.
- The question is about fine-tuning, not inference runtime configuration.

## Procedure

1. **Inventory the hardware.** Record: GPU model and total VRAM, RAM capacity and speed (DDR4 vs DDR5, frequency), CPU model and core count, storage type and speed (NVMe PCIe gen 4 vs gen 3 vs SATA SSD). Calculate available VRAM after OS, display driver, and any other running GPU processes: `available_vram = total_vram_GB - os_reserved_GB`. All model loading and routing decisions must fit within this constraint.

2. **Audit the runtime configuration.** For each runtime in scope:

 **Ollama**: check `OLLAMA_MAX_LOADED_MODELS` (default 1; increase only if VRAM supports multiple concurrent models), `OLLAMA_NUM_PARALLEL` (concurrent request handling), `OLLAMA_MAX_VRAM` (VRAM allocation cap), `OLLAMA_KEEP_ALIVE` (model unload timeout — set to `0` if VRAM is shared with other processes). Review the `Modelfile` for each deployed model.

 **llama.cpp / llama-server**: check `-ngl` (number of GPU layers — must equal total layers for full GPU execution), `-c` (context size in tokens), `-t` (CPU thread count — set to physical core count, not hyperthreaded), `--mlock` (lock model in RAM to prevent swap), `--no-mmap` (force full RAM load vs memory-mapped I/O).

 **LM Studio**: check GPU offload percentage, context length, batch size, CPU threads allocated.

 Document current values and compare against the hardware inventory to identify misconfigurations.

3. **Verify model-hardware fit.** Calculate the VRAM requirement for the loaded model at the current quantization level using this formula:

 `model_vram_GB = (parameter_count_B × bits_per_weight / 8) + kv_cache_GB`

 KV cache size:
 `kv_cache_GB = 2 × n_layers × n_heads × head_dim × context_length × batch_size × bytes_per_element / 1e9`

 Example: Llama 3 8B at Q4_K_M (4.5 bits average) ≈ 4.5 GB model weights + 0.5 GB KV cache at 4K context = ~5 GB total. A GPU with 8 GB VRAM can fully load this with 3 GB available for KV cache growth.

 If the model does not fully fit in VRAM: document how many layers will be CPU-offloaded and the expected throughput penalty (CPU offload typically reduces generation speed by 5-20x depending on PCIe bandwidth).

4. **Review quantization selection.** Verify the quantization format (GGUF, GPTQ, AWQ, EXL2) and level is appropriate for the use case:

 | Level | Bits/weight | Quality loss | Use case |
 |---|---|---|---|
 | Q2_K | ~2.6 | Severe | Prototyping only |
 | Q3_K_M | ~3.4 | High | Acceptable only for low-stakes tasks |
 | Q4_K_M | ~4.5 | Minimal | Default for most production use cases |
 | Q5_K_M | ~5.7 | Very low | Use when output quality matters more than memory |
 | Q6_K | ~6.6 | Negligible | Near-lossless with significant memory saving vs Q8 |
 | Q8_0 | ~8.5 | None | Use only when VRAM is not a constraint |

 Flag any use of Q2_K or Q3_K in a production system processing user-facing or consequential outputs without documented quality trade-off acceptance.

5. **Audit context length configuration.** Verify that the configured context length (`-c` / `num_ctx`) meets three conditions:
 - It does not exceed the model's trained context length (running longer than trained produces degraded output)
 - It is sufficient for the use case's expected maximum input + output length
 - The resulting KV cache fits within available VRAM (calculate using formula from step 3)
 Context length is frequently set to a round number without any of these checks. Provide the optimal value for the specific hardware and use case.

6. **Review model routing logic.** If the system routes between local and cloud models, audit the routing criteria:
 - What triggers cloud routing? (task type, token count, latency requirement, data classification label)
 - Is the data classification check performed before the routing decision or after?
 - What is the fallback when the local model is unavailable? Does the fallback inadvertently route sensitive data to a cloud endpoint?
 - Is the routing decision logged with the classification reason?
 Confirm that any data classified as "local only" (PII, confidential, regulated) is never routed to a cloud endpoint under any circumstances, including fallback conditions.

7. **Measure throughput baseline.** Run a timed generation benchmark:
 - Input: a fixed 512-token prompt
 - Output: request exactly 256 tokens
 - Runs: 5 sequential runs
 - Record: time-to-first-token (TTFT) in milliseconds, generation throughput in tokens/second, peak VRAM usage in GB during generation
 Compare against published benchmarks for the same model, quantization, and GPU class. If measured throughput is less than 70% of the expected value, there is a configuration problem (likely CPU offload, insufficient `-ngl`, or memory-mapped I/O overhead).

8. **Verify privacy boundary enforcement.** Confirm the runtime does not exfiltrate request data:
 - Run `tcpdump` or a network monitoring tool during a generation request; confirm no outbound connections are made during inference
 - Check the runtime's telemetry configuration: disable or restrict telemetry to non-sensitive metadata (run count, model name, response time — not prompt content)
 - Verify model weights are stored locally and are not fetched from a CDN on demand during inference (some runtimes stream weights from a remote cache on first load if local storage is unavailable)
 - Check that the runtime's API server binds only to localhost (127.0.0.1) or the intended local network interface — not to 0.0.0.0 unless external access is intentional

9. **Check model update and integrity.** Verify:
 - SHA-256 or SHA-512 hash of each model weight file is recorded and checked against the published hash from the model provider
 - Model updates require a manual review step — no automatic silent updates via cron
 - For Ollama: `ollama pull <model>` is not run automatically in a background job without human review
 - The process for evaluating a new model version before replacing the production model is documented

## Checklist

- [ ] Hardware inventory recorded: GPU model, VRAM total, VRAM available after OS, RAM, CPU, storage type
- [ ] Available VRAM calculated after deducting OS and running process reservation
- [ ] Runtime configuration documented: all key parameters with current values for each runtime in scope
- [ ] Model VRAM requirement calculated using the formula: weights + KV cache at configured context length
- [ ] CPU offload amount documented if model does not fully fit in VRAM; throughput penalty estimated
- [ ] Quantization level verified as appropriate for use case (Q2/Q3 not used in production without justification)
- [ ] Configured context length within model's trained maximum
- [ ] Configured context length sufficient for 95th percentile of expected use-case input + output
- [ ] KV cache at configured context length fits within available VRAM
- [ ] Model routing criteria documented; classification check occurs before routing decision
- [ ] "Local only" data routing confirmed never reaches cloud endpoint including in fallback conditions
- [ ] Routing decisions logged with classification reason
- [ ] Throughput baseline measured: TTFT, tokens/second, peak VRAM; compared to reference benchmarks
- [ ] No outbound network connections during inference confirmed via network monitoring
- [ ] Telemetry restricted to non-sensitive metadata; prompt content not telemetried
- [ ] API server bound to localhost or intended interface only (not 0.0.0.0 unless intentional)
- [ ] Model weight SHA-256 hashes recorded and verified
- [ ] No automatic silent model updates; manual review required for each update

## Common issues & anti-patterns

**VRAM overflow to RAM without understanding the penalty.** The model is configured with `-ngl 99` but does not fit in VRAM. The runtime silently offloads layers to RAM and uses PCIe bandwidth for every forward pass. On PCIe 4.0 x16 (64 GB/s bidirectional), each layer crossing the PCIe bus adds latency. A 7B model with 5 layers offloaded drops from 80 tok/s to 15 tok/s. Reduce `-ngl` to the number that fits entirely in VRAM; it is faster to run fewer layers on GPU than to have constant PCIe traffic.

**Wrong quantization for the task type.** A multi-step reasoning task (code generation, structured analysis) is running on Q2_K to fit a 70B model in 24 GB VRAM. The output fails consistency checks that Q4_K_M of a smaller 13B model would pass. Q2_K of a large model does not outperform Q4_K_M of a smaller model on reasoning tasks — the quantization loss outweighs the parameter count benefit below Q4. Use Q4_K_M as the minimum for any reasoning-heavy task.

**Context length set to maximum for all requests.** The runtime is configured with `num_ctx=128000` for every request because "more context is always better." At 128K context, the KV cache for a Llama 3 8B model consumes approximately 16 GB — more than a consumer GPU's total VRAM. The model runs entirely on CPU. Set context length to the 95th percentile of actual required context for the use case, not the model's theoretical maximum.

**Model routing by capability without privacy classification check.** The router sends simple queries to the local model and complex queries to the cloud model. The complexity check runs first. A complex query containing patient health records is classified as "complex" and routed to the cloud endpoint before any privacy classification is evaluated. Privacy classification must be the first routing gate, not a secondary filter.

**No throughput baseline before optimization.** The team adjusts `num_parallel`, `mlock`, and layer allocation across three sessions without any recorded baseline. They believe performance improved because "it feels faster." Without a recorded TTFT and tokens/second measurement from the original configuration, there is no objective way to verify improvement. Always record the benchmark before the first change.

**Silent model updates via automated pull.** A cron job runs `ollama pull llama3` nightly. The model tag `llama3` is a floating pointer. One night, the upstream model is updated with a new version. The behavioral change is not noticed for two weeks. For production systems, pin to a specific digest: `ollama run llama3@sha256:abc123...` and treat updates as deployments requiring review.

**Telemetry sending prompt content.** LM Studio is configured with default telemetry settings. The telemetry includes "usage analytics" that contain prompt metadata. For a system processing medical records or legal documents, this violates data handling requirements. Audit every telemetry field before enabling the runtime on any sensitive data workload. Disable all telemetry that cannot be confirmed as non-content.

## Required output

Produce a local LLM runtime review report with:

1. **Hardware profile** — table: component, model/spec, capacity, available headroom
2. **Runtime configuration summary** — table: parameter, current value, recommended value, rationale
3. **Model-hardware fit assessment** — calculated VRAM requirement (weights + KV cache), available VRAM, CPU offload amount, throughput impact estimate
4. **Quantization assessment** — current level, task type, quality trade-off verdict, recommended level if change needed
5. **Context length assessment** — configured value, model maximum, use-case 95th percentile, KV cache size, verdict
6. **Routing logic review** — routing criteria, classification-before-routing confirmation, fallback privacy safety, logging status
7. **Throughput baseline** — TTFT (ms), generation speed (tok/s), peak VRAM (GB), reference benchmark comparison
8. **Privacy boundary assessment** — network traffic during inference (clean/findings), telemetry configuration, API binding, verdict
9. **Model integrity status** — hashes recorded (yes/no), update process (manual/automatic), integrity check mechanism
10. **Prioritized recommendation list** — impact (high/medium/low), specific configuration change with exact parameter and value, expected throughput or quality improvement

## Safety

- Do not reconfigure a production local LLM runtime without first testing changes in a non-production environment on a hardware-equivalent machine.
- If the privacy boundary review finds that confidential data has been telemetried or routed to a cloud endpoint due to a misconfigured router, treat this as a data incident — escalate before completing the report.
- Do not recommend Q2 or Q3 quantization for any task producing user-facing, consequential, or regulated outputs without explicit acknowledgment of the quality trade-off from the system owner.
- Do not disable the API authentication layer (if present) to improve latency unless the runtime is bound to loopback only and no other users can reach the API endpoint.
