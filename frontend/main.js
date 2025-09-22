document.getElementById("run-pipeline").addEventListener("click", async () => {
  const output = document.getElementById("output");
  output.textContent = ""; // Clear previous output

  // Get and trim the JSON text from the textarea
  const pipelineText = document.getElementById("pipeline-json").value.trim();

  let pipeline;
  try {
    // Parse the JSON pipeline input
    pipeline = JSON.parse(pipelineText);
  } catch (e) {
    output.textContent = "Invalid JSON: " + e.message;
    return;
  }

  output.textContent = "Running pipeline...";

  try {
    // Send the pipeline JSON to the backend API
    const response = await fetch("http://localhost:8080/api/run-pipeline", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(pipeline),
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.statusText}`);
    }

    // Parse the JSON response
    const data = await response.json();

    console.log("Received data:", data);
    console.log("Result to render:", data.result);

    renderResults(data.result);
  } catch (err) {
    output.textContent = "Error: " + err.message;
  }
});

function renderResults(result) {
  const output = document.getElementById("output");
  output.innerHTML = ""; // Clear existing output

  if (!result || Object.keys(result).length === 0) {
    output.textContent = "";
    return;
  }

  // Cause Probability Bar
  if (result.cause_probability !== undefined) {
    const bar = document.createElement("div");
    bar.innerHTML = `<strong>Cause Probability:</strong> ${(result.cause_probability * 100).toFixed(2)}%`;
    bar.style.width = "100%";
    bar.style.background = "#ddd";
    bar.style.marginTop = "10px";

    const fill = document.createElement("div");
    fill.style.width = `${result.cause_probability * 100}%`;
    fill.style.height = "20px";
    fill.style.background = "#f00";
    bar.appendChild(fill);

    output.appendChild(bar);
  }

  // Confidence Score
  if (result.confidence_score !== undefined) {
    const conf = document.createElement("p");
    conf.innerHTML = `<strong>Confidence Score:</strong> ${(result.confidence_score * 100).toFixed(1)}%`;
    output.appendChild(conf);
  }

  // Segmentation Result
  if (result.segmentation_result) {
    const seg = document.createElement("p");
    seg.innerHTML = `<strong>Segment:</strong> ${result.segmentation_result}`;
    output.appendChild(seg);
  }

  // Customer Flagged
  if (result.customer_flagged !== undefined) {
    const flag = document.createElement("p");
    flag.innerHTML = `<strong>Customer Flagged:</strong> ${result.customer_flagged ? "✅" : "❌"}`;
    output.appendChild(flag);
  }

  // If no known fields found, fallback to raw JSON display
  if (
    result.cause_probability === undefined &&
    result.confidence_score === undefined &&
    !result.segmentation_result &&
    result.customer_flagged === undefined
  ) {
    output.textContent = JSON.stringify(result, null, 2);
  }
}
