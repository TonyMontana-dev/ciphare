"use client";
import React, { useState, useEffect } from "react";
import { Title } from "../components/title";
import { ErrorMessage } from "../components/error";

export default function Decode() {
  const [fileID, setFileID] = useState(""); // State for file ID input
  const [password, setPassword] = useState(""); // State for password input
  const [algorithm, setAlgorithm] = useState("AES256"); // Default algorithm selection
  const [decryptedFile, setDecryptedFile] = useState<{ data: string; name: string; type: string } | null>(null); // State for the decrypted file
  const [loading, setLoading] = useState(false); // Loading state
  const [error, setError] = useState<string | null>(null); // Error state

  // Use relative URLs in production, absolute URLs in development
  const API_BASE_URL = 
    typeof window !== 'undefined' && window.location.hostname === 'localhost'
      ? process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:3000"
      : ""; // Empty string means relative URLs

  // Extract file ID from URL path, hash, or query params
  useEffect(() => {
    if (typeof window !== 'undefined') {
      // Check URL path parameter first (for /decode/[fileId] format)
      const pathParts = window.location.pathname.split('/');
      const decodeIndex = pathParts.indexOf('decode');
      if (decodeIndex !== -1 && decodeIndex < pathParts.length - 1) {
        const fileIdFromPath = pathParts[decodeIndex + 1];
        if (fileIdFromPath && fileIdFromPath !== '') {
          setFileID(decodeURIComponent(fileIdFromPath));
          return;
        }
      }
      
      // Check URL hash (for legacy /decode#[fileId] format)
      const hash = window.location.hash.slice(1);
      if (hash) {
        setFileID(decodeURIComponent(hash));
        return;
      }
      
      // Check query params (for /decode?id=[fileId] format)
      const urlParams = new URLSearchParams(window.location.search);
      const idFromParams = urlParams.get('id');
      if (idFromParams) {
        setFileID(decodeURIComponent(idFromParams));
      }
    }
  }, []);

  // Handle the decryption process
  const handleDecrypt = async () => {
    if (!fileID || !password) {
      setError("File ID and password are required.");
      return;
    }

    setLoading(true);
    setError(null);
    setDecryptedFile(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/decode/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_id: fileID,
          password,
          algorithm,
        }),
      });

      if (!response.ok) {
        // Try to get error message from response
        let errorMessage = "Decryption failed. Please check your file ID, password, and algorithm.";
        try {
          const errorData = await response.json();
          if (errorData.error) {
            errorMessage = errorData.error;
          }
        } catch {
          // If response is not JSON, use status text
          errorMessage = response.statusText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      const result = await response.json();

      if (!result.decrypted_data || !result.file_name || !result.file_type) {
        throw new Error("Incomplete data received from the server.");
      }

      setDecryptedFile({
        data: result.decrypted_data,
        name: result.file_name,
        type: result.file_type,
      });

      if (result.remaining_reads === 0) {
        setError("This file has been deleted after reaching the maximum number of reads.");
      }
      
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  // Handle file download after decryption
  const handleDownload = () => {
    if (!decryptedFile) return;

    const binaryData = Uint8Array.from(atob(decryptedFile.data), (c) => c.charCodeAt(0));
    const blob = new Blob([binaryData], { type: decryptedFile.type });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = decryptedFile.name;
    link.click();
    URL.revokeObjectURL(url);
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

        {/* Decrypted File Section */}
        {decryptedFile && (
          <div className="mt-8 p-4 bg-zinc-800 border border-zinc-700 rounded text-zinc-300">
            <p className="font-semibold">Decrypted File:</p>
            <p>{decryptedFile.name}</p>
            <button
              onClick={handleDownload}
              className="mt-4 bg-zinc-200 text-zinc-900 rounded px-4 py-2"
            >
              Download File
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
