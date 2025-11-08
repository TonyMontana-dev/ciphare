/**
 * This file redirects users to the decode page with the fileId as a parameter.
 */
import { redirect } from "next/navigation";

// Adjusting to Next.js's async expectations
export default async function Page({ params }: { params: Promise<{ compositeKey: string }> }) {
  const resolvedParams = await params; // Resolve the promise
  const { compositeKey } = resolvedParams;

  // Redirect to decode page with file ID as query parameter
  redirect(`/decode?id=${encodeURIComponent(compositeKey)}`);
}

