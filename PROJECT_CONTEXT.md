# Project context

The active system is the Python invoice engine in `app/`, centered on local LM Studio inference in `app/invoice_worker.py`. `app/invoice_prepare.py` uses Poppler to extract existing PDF text and render pages that need visual reading; the local vision-capable model reads those page images. The supervisor watches the synchronized intake folder and routes results. The model handles the variable invoice layouts; deterministic code enforces the output contract, normalizes supported values, checks consistency and routes exceptions for review.

There is no Tesseract OCR stage, no invoice-family parser, and no JavaScript processing pipeline in the active design. The earlier JavaScript/Tesseract prototype has been removed from this repository. Do not reintroduce its fixed-layout parsing as the extraction strategy.

The target product extends invoice evidence extraction to multi-document customs cases, an approved versioned HTS/PGA/OGA reference dataset, reviewed classification decisions, and draft 3461/7501 generation. The external dataset is not yet available. Until it is integrated, classification and agency matching must fail closed as unavailable. See `docs/Current-to-3461-7501-Architecture.md` and `docs/Customs-Entry-Roadmap.md` for planned stages and acceptance gates.

The active engine requires Python, Poppler, Windows/OneDrive/Power Automate integration, and LM Studio with the configured local model. It does not require Node.js, Tesseract, Ollama, or a vector database. Qdrant is only a possible future candidate-retrieval component after the reference corpus exists and benchmark results justify it.
