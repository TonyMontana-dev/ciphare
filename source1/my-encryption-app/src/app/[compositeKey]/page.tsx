/**
 * This file is needed to redirect the user to the decode page with the fileId as a parameter.
 * 
 */

import { redirect } from "next/navigation";

export default async function Page({ params }: { params: { compositeKey: string } }) {
  const { compositeKey } = params;
  return redirect(`/decode#${compositeKey}`);
}
