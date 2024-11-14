/**
 * This file is needed to redirect the user to the decode page with the fileId as a parameter.
 * 
 */

import { redirect } from "next/navigation";

export default function Page(props: { params: { fileId: string } }) {
  return redirect(`/decode#${props.params.fileId}`);
}
