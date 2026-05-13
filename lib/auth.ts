import { SignJWT, jwtVerify } from "jose";
import { cookies } from "next/headers";

// Resolve JWT secret. In production, JWT_SECRET MUST be set — fail loudly
// if missing so we never sign sessions with a known-public fallback.
function resolveSecret(): Uint8Array {
  const raw = process.env.JWT_SECRET;
  if (raw && raw.length >= 32) {
    return new TextEncoder().encode(raw);
  }
  if (process.env.NODE_ENV === "production") {
    throw new Error(
      "JWT_SECRET environment variable is required in production " +
        "(must be at least 32 characters). Set it in your Vercel project " +
        "settings → Environment Variables. Generate one with: openssl rand -hex 32"
    );
  }
  // Dev-only fallback so local `npm run dev` works without setup friction.
  return new TextEncoder().encode("meridian-hr-dev-only-do-not-use-in-prod-x");
}

const SECRET = resolveSecret();
const COOKIE_NAME = "meridian_session";
const COOKIE_MAX_AGE = 60 * 60 * 24 * 7;

export type SessionPayload = {
  sub: string;
  email: string;
  name: string;
  role: string;
};

export async function signSession(payload: SessionPayload) {
  return await new SignJWT(payload as unknown as Record<string, unknown>)
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime("7d")
    .sign(SECRET);
}

export async function verifySession(token: string): Promise<SessionPayload | null> {
  try {
    const { payload } = await jwtVerify(token, SECRET);
    return payload as unknown as SessionPayload;
  } catch {
    return null;
  }
}

export async function setSessionCookie(token: string) {
  const store = await cookies();
  store.set(COOKIE_NAME, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: COOKIE_MAX_AGE,
  });
}

export async function clearSessionCookie() {
  const store = await cookies();
  store.delete(COOKIE_NAME);
}

export async function getSession(): Promise<SessionPayload | null> {
  const store = await cookies();
  const token = store.get(COOKIE_NAME)?.value;
  if (!token) return null;
  return await verifySession(token);
}

export const SESSION_COOKIE_NAME = COOKIE_NAME;
