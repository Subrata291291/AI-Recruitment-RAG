const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";


export async function matchCandidates({
  companyId,
  file,
  topK,
}) {
  if (!companyId || !companyId.trim()) {
    throw new Error("Company ID is required.");
  }

  if (!file) {
    throw new Error("Job description PDF is required.");
  }

  const formData = new FormData();

  formData.append("company_id", companyId.trim());
  formData.append("file", file);

  if (topK !== undefined && topK !== null) {
    formData.append("top_k", String(topK));
  }

  const response = await fetch(
    `${API_BASE_URL}/matching`,
    {
      method: "POST",
      body: formData,
    }
  );

  let data;

  try {
    data = await response.json();
  } catch {
    throw new Error(
      `Server returned an invalid response (${response.status}).`
    );
  }

  if (!response.ok) {
    throw new Error(
      data?.detail || "Candidate matching failed."
    );
  }

  return data;
}


export async function getCandidates(companyId) {
  if (!companyId || !companyId.trim()) {
    throw new Error("Company ID is required.");
  }

  const response = await fetch(
    `${API_BASE_URL}/candidates?company_id=${encodeURIComponent(
      companyId.trim()
    )}`
  );

  let data;

  try {
    data = await response.json();
  } catch {
    throw new Error(
      `Server returned an invalid response (${response.status}).`
    );
  }

  if (!response.ok) {
    throw new Error(
      data?.detail || "Failed to fetch candidates."
    );
  }

  return data;
}


export async function getCandidate({
  companyId,
  candidateId,
}) {
  if (!companyId || !companyId.trim()) {
    throw new Error("Company ID is required.");
  }

  if (!candidateId || !candidateId.trim()) {
    throw new Error("Candidate ID is required.");
  }

  const response = await fetch(
    `${API_BASE_URL}/candidates/${encodeURIComponent(
      candidateId.trim()
    )}?company_id=${encodeURIComponent(
      companyId.trim()
    )}`
  );

  let data;

  try {
    data = await response.json();
  } catch {
    throw new Error(
      `Server returned an invalid response (${response.status}).`
    );
  }

  if (!response.ok) {
    throw new Error(
      data?.detail || "Failed to fetch candidate."
    );
  }

  return data;
}


export async function checkHealth() {
  const response = await fetch(
    `${API_BASE_URL}/health`
  );

  if (!response.ok) {
    throw new Error("Backend health check failed.");
  }

  return response.json();
}