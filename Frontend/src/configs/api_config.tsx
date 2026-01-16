const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

if (!baseUrl) {
    throw new Error("API URL not found");
}

export const system_health = `${baseUrl}/v1/system/health`
export const parse_github_url = `${baseUrl}/v1/features/parse_github_url`
export const parse_github_url_stream = `${baseUrl}/v1/features/parse_github_url/stream`
export const github_analysis = `${baseUrl}/v1/features/analysis`
export const chat_api = `${baseUrl}/v1/features/chat`