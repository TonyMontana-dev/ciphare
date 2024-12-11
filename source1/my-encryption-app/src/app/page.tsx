/**
 * This file is the home page of the application. It displays a brief introduction to the app and provides links to the encryption and community pages.
 * 
 * @returns {JSX.Element} The rendered home page content.
 * 
 */

import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col gap-8 pb-8 md:gap-16 md:pb-16 xl:pb-24">
      <div className="flex flex-col items-center justify-center max-w-3xl px-8 mx-auto mt-8 sm:min-h-screen sm:mt-0 sm:px-0">
        <div>
          <h1 className="py-4 text-5xl font-bold tracking-tight text-center text-transparent bg-gradient-to-t bg-clip-text from-zinc-100/50 to-white sm:text-7xl">
            Encrypt Everything Everytime Securely
          </h1>
          <p className="mt-6 leading-5 text-zinc-600 sm:text-center">
            Your files are encrypted before they are stored, ensuring privacy and security. Encrypted data remains secure for a limited time and read operations.
          </p>
          <div className="flex flex-col justify-center gap-4 mx-auto mt-8 sm:flex-row sm:max-w-lg ">
            <Link
              href="/encode"
              className="sm:w-1/2 sm:text-center inline-block space-x-2 rounded px-4 py-1.5 md:py-2 text-base font-semibold leading-7 text-white ring-1 ring-zinc-600 hover:bg-white hover:text-zinc-900 duration-150 hover:ring-white hover:drop-shadow-cta"
            >
              Encrypt
            </Link>
            <Link
              href="/community"
              className="sm:w-1/2 sm:text-center inline-block transition-all space-x-2 rounded px-4 py-1.5 md:py-2 text-base font-semibold leading-7 text-zinc-800 bg-zinc-50 ring-1 ring-transparent hover:text-zinc-100 hover:ring-zinc-600/80 hover:bg-zinc-900/20 duration-150 hover:drop-shadow-cta"
            >
              <span>Join Us</span>
              <span aria-hidden="true">&rarr;</span>
            </Link>
          </div>
        </div>
      </div>
      <h2 className="py-4 text-3xl font-bold text-center text-zinc-300 ">Follow us to get updates when new version of Ciphare are available.</h2>
    </div>
  );
}
