"use client";
import React, { useState } from "react";
import { Title } from "../components/title";
import { ErrorMessage } from "../components/error";

export default function Decode() {
  const [fileID, setFileID] = useState(""); // Initialize fileID state as an empty string
  const [password, setPassword] = useState(""); // Initialize password state as an empty string
  const [algorithm, setAlgorithm] = useState("AES256"); // Default algorithm selection
  const [decryptedFile, setDecryptedFile] = useState<{ data: string; name: string; type: string } | null>(null); // Initialize decryptedFile as null
  const [loading, setLoading] = useState(false); // Initialize loading state as false
  const [error, setError] = useState<string | null>(null); // Initialize error state as null

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:3000"; // Default to local server URL if not provided in environment variables

  // Function to handle decryption of the file using the API endpoint
  const handleDecrypt = async () => {
    if (!fileID || !password) {
      setError("File ID and password are required.");
      return;
    }

    // Reset state values before the decryption process starts
    setLoading(true);
    setError(null);
    setDecryptedFile(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/decode`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_id: fileID,
          password,
          algorithm,
        }),
      });

      if (!response.ok) throw new Error("Decryption failed. Please check your file ID, password, and algorithm.");

      const result = await response.json();

      // Check if all necessary data is returned
      if (!result.decrypted_data || !result.file_name || !result.file_type) {
        throw new Error("Incomplete data received from the server.");
      }

      // Set the decrypted file data, name, and type
      setDecryptedFile({
        data: result.decrypted_data,
        name: result.file_name,
        type: result.file_type,
      });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  // Function to handle file download after decryption is successful
  const handleDownload = () => {
    if (!decryptedFile) return;

    const binaryData = Uint8Array.from(atob(decryptedFile.data), (c) => c.charCodeAt(0)); // Decode base64 data to binary array buffer
    const blob = new Blob([binaryData], { type: decryptedFile.type }); // Create a Blob from the binary data
    const url = URL.createObjectURL(blob); // Create a URL for the Blob data

    const link = document.createElement("a"); // Create a temporary link element for download
    link.href = url; // Set the URL as the link's href
    link.download = decryptedFile.name; // Use original file name
    link.click(); // Simulate a click on the link to trigger download
    URL.revokeObjectURL(url); // Revoke the URL object after download
  };

  return (
    <div className="container px-8 mx-auto mt-16 lg:mt-32">
      {error && <ErrorMessage message={error} />}

      <div className="max-w-3xl mx-auto">
        <Title>Decrypt a File</Title>

        {/* File ID Input */}
        <div className="mt-8">
          <label htmlFor="fileID" className="block text-xs font-medium text-zinc-100">
            File ID
          </label>
          <input
            type="text"
            id="fileID"
            className="w-full p-2 mt-1 bg-zinc-900 border border-zinc-700 rounded text-zinc-300"
            value={fileID}
            onChange={(e) => setFileID(e.target.value)}
          />
        </div>

        {/* Password Input */}
        <div className="mt-4">
          <label htmlFor="password" className="block text-xs font-medium text-zinc-100">
            Password for Decryption
          </label>
          <input
            type="password"
            id="password"
            className="w-full p-2 mt-1 bg-zinc-900 border border-zinc-700 rounded text-zinc-300"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
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

        {/* Decrypt Button */}
        <button
          onClick={handleDecrypt}
          disabled={loading}
          className={`mt-6 w-full h-12 flex items-center justify-center text-base font-semibold bg-zinc-200 text-zinc-900 rounded hover:bg-zinc-900 hover:text-zinc-100 ${
            loading ? "animate-pulse" : ""
          }`}
        >
          {loading ? "Decrypting..." : "Decrypt"}
        </button>

        {/* Decrypted File Information */}
        {decryptedFile && (
          <div className="mt-8 p-4 bg-zinc-800 border border-zinc-700 rounded text-zinc-300">
            <p className="font-semibold">Decrypted File:</p>
            <p>{decryptedFile.name}</p>
            <button onClick={handleDownload} className="mt-4 bg-zinc-200 text-zinc-900 rounded px-4 py-2">
              Download File
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
