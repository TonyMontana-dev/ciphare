/**
 * This file is needed to redirect the user to the decode page with the fileId as a parameter.
 * 
 */

import { redirect } from "next/navigation";

interface Props {
  params: {
    compositeKey: string; // Match the folder `[compositeKey]`
  };
}

export default function Page({ params }: Props) {
  const { compositeKey } = params;
  return redirect(`/decode#${compositeKey}`);
}
