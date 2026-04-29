const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const projectRoot = path.resolve(__dirname, "..");

const pipelineName = "Data Hermetica Private Document Intelligence Pipeline";
const pipelineVersion = "v0.1";

const pipelineSteps = [
  {
    stepNumber: 1,
    name: "OCR PDF invoices with Tesseract",
    script: "ocr-pdf-with-tesseract.js",
    expectedOutputs: [
      path.join("ocr", "tesseract-ocr-run-summary.json"),
      path.join("ocr", "sample-commercial-invoice-001-tesseract-ocr.txt"),
      path.join("ocr", "sample-commercial-invoice-002-tesseract-ocr.txt"),
      path.join("ocr", "sample-commercial-invoice-003-tesseract-ocr.txt"),
      path.join("ocr", "sample-commercial-invoice-004-tesseract-ocr.txt"),
      path.join("ocr", "sample-commercial-invoice-005-tesseract-ocr.txt")
    ]
  },
  {
    stepNumber: 2,
    name: "Segment OCR invoice items",
    script: "segment-ocr-invoice-items.js",
    expectedOutputs: [
      path.join("ocr", "segmented-items-summary.json"),
      path.join("ocr", "sample-commercial-invoice-001-segmented-items.json"),
      path.join("ocr", "sample-commercial-invoice-002-segmented-items.json"),
      path.join("ocr", "sample-commercial-invoice-003-segmented-items.json"),
      path.join("ocr", "sample-commercial-invoice-004-segmented-items.json"),
      path.join("ocr", "sample-commercial-invoice-005-segmented-items.json")
    ]
  },
  {
    stepNumber: 3,
    name: "Build deterministic canonical rows from segmented Honeywell invoices",
    script: "build-canonical-rows-from-segments.js",
    expectedOutputs: [
      path.join("outputs", "deterministic-canonical-lines-summary.json"),
      path.join("outputs", "sample-commercial-invoice-001-deterministic-canonical-lines.json"),
      path.join("outputs", "sample-commercial-invoice-001-deterministic-canonical-lines.csv"),
      path.join("outputs", "sample-commercial-invoice-002-deterministic-canonical-lines.json"),
      path.join("outputs", "sample-commercial-invoice-002-deterministic-canonical-lines.csv"),
      path.join("outputs", "sample-commercial-invoice-003-deterministic-canonical-lines.json"),
      path.join("outputs", "sample-commercial-invoice-003-deterministic-canonical-lines.csv")
    ]
  },
  {
    stepNumber: 4,
    name: "Build canonical rows for special invoice families",
    script: "build-canonical-rows-for-special-families.js",
    expectedOutputs: [
      path.join("outputs", "special-family-canonical-lines-summary.json"),
      path.join("outputs", "sample-commercial-invoice-004-special-family-canonical-lines.json"),
      path.join("outputs", "sample-commercial-invoice-004-special-family-canonical-lines.csv"),
      path.join("outputs", "sample-commercial-invoice-005-special-family-canonical-lines.json"),
      path.join("outputs", "sample-commercial-invoice-005-special-family-canonical-lines.csv")
    ]
  },
  {
    stepNumber: 5,
    name: "Build master canonical JSON and CSV output",
    script: "build-master-canonical-output.js",
    expectedOutputs: [
      path.join("outputs", "master-canonical-invoice-lines.json"),
      path.join("outputs", "master-canonical-invoice-lines.csv")
    ]
  }
];

const outputDirectories = [
  "outputs",
  "ocr",
  "images"
];

function ensureDirectoryExists(directoryPath) {
  if (!fs.existsSync(directoryPath)) {
    fs.mkdirSync(directoryPath, { recursive: true });
  }
}

function readJsonIfExists(relativePath) {
  const fullPath = path.join(projectRoot, relativePath);

  if (!fs.existsSync(fullPath)) {
    return null;
  }

  try {
    return JSON.parse(fs.readFileSync(fullPath, "utf8"));
  } catch (error) {
    return {
      error: `Could not parse JSON file: ${relativePath}`,
      detail: error.message
    };
  }
}

function fileExists(relativePath) {
  return fs.existsSync(path.join(projectRoot, relativePath));
}

function getFileSize(relativePath) {
  const fullPath = path.join(projectRoot, relativePath);

  if (!fs.existsSync(fullPath)) {
    return null;
  }

  return fs.statSync(fullPath).size;
}

function runNodeScript(step) {
  const scriptPath = path.join(projectRoot, "src", step.script);

  if (!fs.existsSync(scriptPath)) {
    throw new Error(`Script not found: ${scriptPath}`);
  }

  console.log("============================================================");
  console.log(`STEP ${step.stepNumber}: ${step.name}`);
  console.log(`Running: node src\\${step.script}`);
  console.log("============================================================");

  const startedAt = Date.now();

  const result = spawnSync(
    process.execPath,
    [scriptPath],
    {
      cwd: projectRoot,
      stdio: "inherit",
      shell: false,
      windowsHide: false
    }
  );

  const finishedAt = Date.now();

  if (result.error) {
    throw new Error(`Failed to run ${step.script}: ${result.error.message}`);
  }

  if (result.status !== 0) {
    throw new Error(`${step.script} exited with code ${result.status}`);
  }

  const outputChecks = step.expectedOutputs.map((relativePath) => {
    return {
      path: relativePath,
      exists: fileExists(relativePath),
      sizeBytes: getFileSize(relativePath)
    };
  });

  const missingOutputs = outputChecks.filter((output) => !output.exists);

  if (missingOutputs.length > 0) {
    throw new Error(
      `Step ${step.stepNumber} completed but expected outputs are missing: ${missingOutputs
        .map((output) => output.path)
        .join(", ")}`
    );
  }

  return {
    stepNumber: step.stepNumber,
    name: step.name,
    script: step.script,
    status: "completed",
    startedAt: new Date(startedAt).toISOString(),
    finishedAt: new Date(finishedAt).toISOString(),
    durationMs: finishedAt - startedAt,
    expectedOutputs: outputChecks
  };
}

function collectPipelineMetrics() {
  const ocrSummary = readJsonIfExists(path.join("ocr", "tesseract-ocr-run-summary.json"));
  const segmentationSummary = readJsonIfExists(path.join("ocr", "segmented-items-summary.json"));
  const deterministicSummary = readJsonIfExists(path.join("outputs", "deterministic-canonical-lines-summary.json"));
  const specialFamilySummary = readJsonIfExists(path.join("outputs", "special-family-canonical-lines-summary.json"));

  const deterministicJobs = deterministicSummary && Array.isArray(deterministicSummary.jobs)
    ? deterministicSummary.jobs
    : [];

  const specialFamilyJobs = specialFamilySummary && Array.isArray(specialFamilySummary.jobs)
    ? specialFamilySummary.jobs
    : [];

  const allCanonicalJobs = [
    ...deterministicJobs.map((job) => {
      return {
        source: "deterministic_segments",
        jobName: job.jobName,
        invoiceNumber: job.invoiceNumber || "N/A",
        invoiceDate: job.invoiceDate || "N/A",
        shipmentNumber: job.shipmentNumber || "N/A",
        expectedRows: job.expectedRows,
        actualRows: job.actualRows,
        validationFlagCount: job.validationFlagCount,
        jsonOutputFile: job.jsonOutputFile,
        csvOutputFile: job.csvOutputFile
      };
    }),
    ...specialFamilyJobs.map((job) => {
      return {
        source: "special_family_parser",
        jobName: job.jobName,
        family: job.family,
        invoiceNumber: job.invoiceMetadata?.invoiceNumber || "N/A",
        invoiceDate: job.invoiceMetadata?.invoiceDate || "N/A",
        shipmentNumber: job.invoiceMetadata?.containerNumber || "N/A",
        expectedRows: job.expectedRows,
        actualRows: job.actualRows,
        validationFlagCount: job.validationFlagCount,
        jsonOutputFile: job.jsonOutputFile,
        csvOutputFile: job.csvOutputFile
      };
    })
  ];

  const totalRowsExtracted = allCanonicalJobs.reduce((sum, job) => {
    return sum + (typeof job.actualRows === "number" ? job.actualRows : 0);
  }, 0);

  const totalValidationFlags = allCanonicalJobs.reduce((sum, job) => {
    return sum + (typeof job.validationFlagCount === "number" ? job.validationFlagCount : 0);
  }, 0);

  const totalExpectedRows = allCanonicalJobs.reduce((sum, job) => {
    return sum + (typeof job.expectedRows === "number" ? job.expectedRows : 0);
  }, 0);

  const allRowCountsMatched = allCanonicalJobs.every((job) => {
    return job.expectedRows === job.actualRows;
  });

  const allValidationClear = allCanonicalJobs.every((job) => {
    return job.validationFlagCount === 0;
  });

  return {
    ocrSummary,
    segmentationSummary,
    deterministicSummary,
    specialFamilySummary,
    canonicalExtractionJobs: allCanonicalJobs,
    metrics: {
      pdfJobCount: ocrSummary && Array.isArray(ocrSummary.jobs) ? ocrSummary.jobs.length : null,
      segmentationJobCount: segmentationSummary && Array.isArray(segmentationSummary.jobs) ? segmentationSummary.jobs.length : null,
      canonicalJobCount: allCanonicalJobs.length,
      totalExpectedRows,
      totalRowsExtracted,
      totalValidationFlags,
      allRowCountsMatched,
      allValidationClear
    }
  };
}

function writeMasterSummary(pipelineStartedAt, pipelineFinishedAt, stepResults, pipelineStatus, errorMessage = null) {
  const collected = collectPipelineMetrics();

  const summary = {
    pipelineName,
    pipelineVersion,
    status: pipelineStatus,
    startedAt: new Date(pipelineStartedAt).toISOString(),
    finishedAt: new Date(pipelineFinishedAt).toISOString(),
    durationMs: pipelineFinishedAt - pipelineStartedAt,
    errorMessage,
    steps: stepResults,
    metrics: collected.metrics,
    canonicalExtractionJobs: collected.canonicalExtractionJobs,
    sourceSummaries: {
      ocrSummaryPath: path.join("ocr", "tesseract-ocr-run-summary.json"),
      segmentationSummaryPath: path.join("ocr", "segmented-items-summary.json"),
      deterministicSummaryPath: path.join("outputs", "deterministic-canonical-lines-summary.json"),
      specialFamilySummaryPath: path.join("outputs", "special-family-canonical-lines-summary.json")
    },
    generatedOutputFiles: {
      masterSummary: path.join("outputs", "master-pipeline-run-summary.json"),
      jsonAndCsvOutputsDirectory: "outputs",
      ocrDirectory: "ocr",
      imagesDirectory: "images"
    }
  };

  const summaryPath = path.join(projectRoot, "outputs", "master-pipeline-run-summary.json");
  fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2), "utf8");

  return summary;
}

function printFinalSummary(summary) {
  console.log("============================================================");
  console.log(`${pipelineName} ${pipelineVersion}`);
  console.log("PIPELINE RUN COMPLETE");
  console.log("============================================================");
  console.log(`Status: ${summary.status}`);
  console.log(`Duration ms: ${summary.durationMs}`);
  console.log(`Canonical jobs: ${summary.metrics.canonicalJobCount}`);
  console.log(`Expected rows: ${summary.metrics.totalExpectedRows}`);
  console.log(`Rows extracted: ${summary.metrics.totalRowsExtracted}`);
  console.log(`Validation flags: ${summary.metrics.totalValidationFlags}`);
  console.log(`All row counts matched: ${summary.metrics.allRowCountsMatched}`);
  console.log(`All validation clear: ${summary.metrics.allValidationClear}`);
  console.log("Master summary:");
  console.log(path.join(projectRoot, "outputs", "master-pipeline-run-summary.json"));
  console.log("============================================================");
}

function main() {
  const pipelineStartedAt = Date.now();
  const stepResults = [];

  try {
    for (const directory of outputDirectories) {
      ensureDirectoryExists(path.join(projectRoot, directory));
    }

    for (const step of pipelineSteps) {
      const result = runNodeScript(step);
      stepResults.push(result);
    }

    const pipelineFinishedAt = Date.now();
    const summary = writeMasterSummary(
      pipelineStartedAt,
      pipelineFinishedAt,
      stepResults,
      "completed",
      null
    );

    printFinalSummary(summary);
  } catch (error) {
    const pipelineFinishedAt = Date.now();

    const summary = writeMasterSummary(
      pipelineStartedAt,
      pipelineFinishedAt,
      stepResults,
      "failed",
      error.message
    );

    console.error("============================================================");
    console.error(`${pipelineName} ${pipelineVersion}`);
    console.error("PIPELINE RUN FAILED");
    console.error("============================================================");
    console.error(error.message);
    console.error("Partial master summary:");
    console.error(path.join(projectRoot, "outputs", "master-pipeline-run-summary.json"));
    console.error("============================================================");

    process.exit(1);
  }
}

main();