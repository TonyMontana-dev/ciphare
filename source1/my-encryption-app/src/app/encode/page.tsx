"use client";
import React, { useState } from "react";
import { Title } from "../components/title";
import { ErrorMessage } from "../components/error";

export default function Encode() {
  const [file, setFile] = useState<File | null>(null);  // Initialize file as null
  const [password, setPassword] = useState("");  // Initialize password as an empty string
  const [reads, setReads] = useState(0); // 0 for unlimited reads
  const [ttl, setTtl] = useState(1);  // Default to 1 day
  const [ttlMultiplier, setTtlMultiplier] = useState(86400); // Default to days in seconds
  const [algorithm, setAlgorithm] = useState("AES256"); // Default algorithm
  const [shareLink, setShareLink] = useState<string | null>(null);  // Initialize shareLink as null
  const [loading, setLoading] = useState(false);  // Initialize loading as false
  const [error, setError] = useState<string | null>(null);  // Initialize error as null

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:3000"; // Default to local server URL if not provided in environment variables

  // Helper function to convert ArrayBuffer to Base64 string
  const arrayBufferToBase64 = (buffer: ArrayBuffer): string => {
    let binary = "";
    const bytes = new Uint8Array(buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  };

  // Handle file upload event and set the selected file
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFile(file);
      setError(null);
    }
  };

  // Handle the encryption process when the user clicks the Encrypt button
  const handleEncrypt = async () => {
    if (!file) {
      setError("Please select a file to encrypt.");
      return;
    }

    // Set loading state, clear error, and share link
    setLoading(true);
    setError(null);
    setShareLink(null);

    try {
      // Convert the file to a Base64 string using FileReader API
      const fileData = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(arrayBufferToBase64(reader.result as ArrayBuffer)); // Efficient Base64 conversion
        reader.onerror = reject;
        reader.readAsArrayBuffer(file); // Read the file as an ArrayBuffer
      });

      // Send the Base64-encoded file data, along with name and type, to the backend
      console.log("Payload:", {
        file_data: fileData,
        file_name: file.name,
        file_type: file.type,
        password,
        reads,
        ttl: ttl * ttlMultiplier,
        algorithm,
      });

      const response = await fetch(`${API_BASE_URL}/api/encode/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_data: fileData,
          file_name: file.name, // Original file name
          file_type: file.type, // Original file type
          password, // Encryption password
          reads, // Number of reads
          ttl: ttl * ttlMultiplier, // Convert TTL to seconds
          algorithm, // Selected algorithm
        }),
      });

      if (!response.ok) throw new Error("Encryption failed. Please try again.");

      const result = await response.json();
      const domain = "https://ciphare.vercel.app"; // Adjust this to your deployment domain
      setShareLink(`${domain}/decode/${result.file_id}`); // Set the shareable link for decryption
    } catch (e) {
      console.error("Error during encryption:", e);
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container px-8 mx-auto mt-16 lg:mt-32">
      {error && <ErrorMessage message={error} />}

      <div className="max-w-3xl mx-auto">
        <Title>Encrypt and Share</Title>

        {/* File Input */}
        <div className="mt-8">
          <label className="block text-xs font-medium text-zinc-100">
            Upload File to Encrypt
          </label>
          <input
            type="file"
            className="w-full p-2 mt-1 bg-zinc-900 border border-zinc-700 rounded text-zinc-300"
            onChange={handleFileUpload}
          />
        </div>

        {/* Password Input */}
        <div className="mt-4">
          <label htmlFor="password" className="block text-xs font-medium text-zinc-100">
            Password for Encryption
          </label>
          <input
            type="password"
            id="password"
            className="w-full p-2 mt-1 bg-zinc-900 border border-zinc-700 rounded text-zinc-300"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        {/* Reads and TTL */}
        <div className="flex flex-col sm:flex-row gap-4 mt-4">
          <div className="w-full">
            <label htmlFor="reads" className="block text-xs font-medium text-zinc-100">
              Reads (0 for unlimited)
            </label>
            <input
              type="number"
              id="reads"
              className="w-full p-2 bg-zinc-900 border border-zinc-700 rounded text-zinc-300"
              value={reads}
              onChange={(e) => setReads(parseInt(e.target.value))}
            />
          </div>
          {/* Time-to-Live (TTL) */}
          <div className="w-full">
            <label htmlFor="ttl" className="block text-xs font-medium text-zinc-100">
              Time-to-Live (TTL)
            </label>
            <input
              type="number"
              id="ttl"
              className="w-full p-2 bg-zinc-900 border border-zinc-700 rounded text-zinc-300"
              value={ttl}
              onChange={(e) => setTtl(parseInt(e.target.value))}
            />
            <select
              className="w-full mt-2 p-2 bg-zinc-900 border border-zinc-700 rounded text-zinc-300"
              onChange={(e) => setTtlMultiplier(parseInt(e.target.value))}
            >
              <option value={60}>Minutes</option>
              <option value={3600}>Hours</option>
              <option value={86400}>Days</option>
            </select>
          </div>
        </div>

        {/* Algorithm Selection */}
        <div className="mt-4">
          <label htmlFor="algorithm" className="block text-xs font-medium text-zinc-100">
            Select Encryption Algorithm
          </label>
          <select
            id="algorithm"
            className="w-full p-2 mt-1 bg-zinc-900 border border-zinc-700 rounded text-zinc-300"
            value={algorithm}
            onChange={(e) => setAlgorithm(e.target.value)}
          >
            <option value="AES256">AES-256</option>
            {/* Add more algorithms if needed */}
          </select>
        </div>

        {/* Encrypt Button */}
        <button
          onClick={handleEncrypt}
          disabled={loading}
          className={`mt-6 w-full h-12 flex items-center justify-center text-base font-semibold bg-zinc-200 text-zinc-900 rounded hover:bg-zinc-900 hover:text-zinc-100 ${
            loading ? "animate-pulse" : ""
          }`}
        >
          {loading ? "Encrypting..." : "Encrypt"}
        </button>

        {/* Shareable Link */}
        {shareLink && (
          <div className="mt-8 p-4 bg-zinc-800 border border-zinc-700 rounded text-zinc-300">
            <p className="font-semibold">Shareable Link:</p>
            <p className="break-all">{shareLink}</p>
            <p className="mt-2 text-sm">Share this link to allow decryption.</p>
          </div>
        )}
      </div>
    </div>
  );
}
