const express = require("express");
const cors = require("cors");
const { spawn } = require("node:child_process");
const path = require("node:path");

const app = express();

const PORT = Number(process.env.PORT || 3015);
const frontendPath = path.join(__dirname, "..", "dist");

app.use(cors());
app.use(express.json());

app.get("/health", (req, res) => {
  res.json({
    status: "Bushfire AI backend running",
  });
});

app.post("/predict", (req, res) => {
  const { latitude, longitude } = req.body;

  if (
    typeof latitude !== "number" ||
    typeof longitude !== "number"
  ) {
    return res.status(400).json({
      error: "latitude and longitude are required",
    });
  }

  const projectRoot = path.resolve(__dirname, "../..");

  const pythonPath = path.join(
    projectRoot,
    ".venv",
    "bin",
    "python"
  );

  const scriptPath = path.join(
    projectRoot,
    "src",
    "predict_api.py"
  );

  const pythonProcess = spawn(
    pythonPath,
    [
      scriptPath,
      String(latitude),
      String(longitude),
    ],
    {
      cwd: projectRoot,
    }
  );

  let output = "";
  let errorOutput = "";

  pythonProcess.stdout.on("data", (data) => {
    output += data.toString();
  });

  pythonProcess.stderr.on("data", (data) => {
    errorOutput += data.toString();
  });

  pythonProcess.on("close", (code) => {
    if (code !== 0) {
      console.error(errorOutput);

      return res.status(500).json({
        error: "Prediction failed",
      });
    }

    try {
      const result = JSON.parse(output);

      res.json(result);
    } catch (error) {
      console.error("Python output:", output);

      res.status(500).json({
        error: "Invalid prediction response",
      });
    }
  });
});

app.use(express.static(frontendPath));

app.get(/.*/, (req, res) => {
  res.sendFile(path.join(frontendPath, "index.html"));
});

app.listen(PORT, () => {
  console.log(
    `Bushfire AI running on http://localhost:${PORT}`
  );
});
