# HTS and PGA/OGA dictionary placeholder

The authoritative HTS and PGA/OGA dictionary is being developed separately and is not included in this repository. This directory intentionally contains no invented classifications, tariff rates, agency flags, or regulatory advice.

Future dataset delivery must include:

- source agency and official source URL;
- source publication/effective dates and retrieval date;
- version identifier and file checksum;
- HTS code, legal description, hierarchy, units, rates and chapter/legal-note references as licensed/authorized;
- PGA/OGA agency/program flags with applicability conditions, citations and effective dates;
- data dictionary, update procedure, known gaps and provenance;
- reviewed golden examples and expected results.

Until those artifacts are approved and integrated, product matching must return `dataset_status: "unavailable"`, no selected HTS code, no inferred agency flags, and a human-review-required state. Placeholder fixtures in tests may exercise this unavailable state only; they must never resemble usable tariff data.
