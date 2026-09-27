export const analyzeVideo = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch('/api/analyze', {
    method: "POST",
    body: formData,
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || `Server error: ${response.status}`);
  }
  
  return response.json();
};