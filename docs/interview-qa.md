# Interview Q&A — the model fine-tune story

> Facts in every answer below are reproducible from this repo: `evaluation/train_transformer.py`, `evaluation/tickets.json` (92 labeled tickets), `docs/model-comparison.md`, and the training log summary. No claim here goes beyond what the code measures.

## 1. "Bạn fine-tune model ở đâu? Có thật không?"

> Fine-tune trên máy local của tôi — DistilBERT-base-uncased, classification head 5 lớp, trên chính dataset 92 labeled tickets của project. Split stratified theo category với seed 42: 73 train / 19 val. Train 3 epochs (30 steps, batch 8) trên Apple M1 — MPS, khoảng 8 giây. Kết quả: accuracy 1.0 và macro-F1 1.0 trên val split. Toàn bộ script nằm trong `evaluation/train_transformer.py`, artifact gitignored, và `pytest` có sẵn một test tự động chạy khi artifact tồn tại — nên con số này không phải claim, nó được verify lại được.

**Chi tiết kỹ thuật nếu bị hỏi sâu:**
- Loss trung bình qua 3 epochs: ~1.17 (chance level cho 5 lớp là ln 5 ≈ 1.61).
- Không có hyperparameter tuning — đúng nghĩa "minimal fine-tune", lr default của Trainer.
- Artifact không commit vì trọng số (268MB) không thuộc git; fresh checkout vẫn reproduce được bằng 1 lệnh.

## 2. "Sao không fine-tune qua API (OpenAI, Cloudflare, Together)?"

> Ba lý do, theo thứ tự quyết định:
> 1. **Cloudflare Workers AI không có train-via-API.** Cái gọi là "finetune" của họ thực chất là *serving LoRA*: bạn train adapter ở nơi khác (HuggingFace AutoTrain, GPU ngoài), upload `adapter_model.safetensors` + `adapter_config.json` (rank ≤ 8, < 300MB), rồi inference kèm `lora:<id>`. Không phải "bấm API là train".
> 2. **92 labels không đáng chi phí.** Together/Fireworks có LoRA-via-API thật (JSONL dataset, trả tiền token + endpoint hosted), nhưng để host một endpoint cho classifier 5 lớp với 92 samples là overkill — và với dataset nhỏ này, TF-IDF + LogReg đã đạt 1.0 rồi. Fine-tune LLM sẽ chỉ thêm chi phí, không thêm thông tin.
> 3. **OpenAI fine-tune đang wind-down với user mới.** Không chọn path có rủi ro ngừng hỗ trợ cho một project portfolio.
>
> Trong khi đó fine-tune DistilBERT local mất 14 giây, 0 đồng, và cho tôi trải nghiệm train thật để nói chuyện — đó là lựa chọn đúng.

## 3. "DistilBERT và TF-IDF đều 1.0 — vậy tại sao LLM 8B chỉ 79%?"

> Ba con số đó nói đúng điều tôi muốn chứng minh: **taxonomy này hẹp** (5 lớp cố định, ticket pattern ổn định) nên supervised nhỏ đã giải quyết trọn. Llama 3.1 8B inference qua prompt đạt 79.3% / 0.78 macro-F1 — nhầm lẫn tập trung ở cặp refund↔payment vì hai loại ticket dùng từ ngữ gần nhau, và prompt không "nhớ" boundary như supervised học từ labels. Bài học rút ra (nói được thành câu): *khi có labeled data, classifier nhỏ supervised thắng LLM-thông-dịch prompt-based trên tác vụ hẹp; LLM hợp lý ở chỗ không cần labels và xử lý open-ended.* Đó là lý do prod dùng LLM cho summary + draft reply, còn classification chỉ là một prompt có schema-validated output.

## 4. "LLM trong prod là gì — tại sao không dùng fine-tuned model trong API?"

> Prod chạy Cloudflare Workers AI llama-3.1-8b qua `AI_PROVIDER=cloudflare` (có stub offline + OpenAI-compatible option). Fine-tuned DistilBERT nằm ở *evaluation layer*, không phải serving layer — đây là quyết định kiến trúc, không phải thiếu năng lực serving:
> - LLM làm được nhiều việc mà classifier 5 lớp không làm: **summary** và **draft reply** (có grounding vào ticket + policy + similar tickets).
> - Toàn bộ AI là **suggestion-only**: output schema-validated, guardrail fail-closed (prompt steering, refund promise, hallucinated policy đều bị reject → 502, ticket untouched). Agent vẫn là người gửi và quyết.
> - `ai_predictions` log model + confidence, nên mọi prediction đều audit được.

## 5. "Con số 1.0 có đáng tin không?" (câu hỏi phản biện quan trọng nhất)

> Không đáng tin *như một benchmark* — và tôi là người đầu tiên nói điều đó. Val chỉ có 19 samples, TF-IDF cũng đạt 1.0 trên cùng split, tức là dataset-specific. Giá trị thật của bảng số này là **quy trình**: cùng 92 tickets, cùng split, cùng metric — đo cả stub, TF-IDF, DistilBERT fine-tune, và LLM 8B, rồi báo cáo cả con số xấu (79% của LLM) một cách công khai. Tôi muốn được đánh giá ở việc "biết cách đo và không tự lừa mình bằng perfect score", không phải ở con số 1.0.
