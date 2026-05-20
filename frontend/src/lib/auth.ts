import api from "./api";

export interface UserProfile {
  id: string;
  nome: string;
  email: string;
  role: string;
  totp_ativado: boolean;
}

export async function login(email: string, senha: string) {
  const { data } = await api.post("/auth/login", { email, senha });
  return data;
}

export async function verifyMfa(codigo: string, temp_token: string) {
  const { data } = await api.post("/auth/mfa/verify", { codigo, temp_token });
  return data;
}

export async function getMe(): Promise<UserProfile> {
  const { data } = await api.get("/auth/me");
  return data;
}

export function saveToken(token: string) {
  localStorage.setItem("access_token", token);
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("user");
  window.location.href = "/login";
}

export function isAuthenticated(): boolean {
  return !!getToken();
}
