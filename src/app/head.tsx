export default function Head({ title, subtitle }: { title?: string; subtitle?: string }) {
    // Set defaults specific to your project if title/subtitle aren't provided
    title ??= "Secure File Encryption and Sharing";
    subtitle ??= "Ciphare - Encrypt and share files securely with state-of-the-art encryption algorithms.";
  
    // Determine base URL based on environment (development vs. production) for Open Graph image generation
    // Replace "http://localhost:3000" with your production URL if needed
    // For Vercel deployments, use the Vercel URL provided by the VERCEL_URL environment variable (if available) to support preview deployments and custom domains (e.g., "https://my-app.vercel.app")
    const baseUrl = process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : "http://localhost:3000";
  
    // Generate URL for Open Graph image generation
    const ogImageUrl = new URL("/api/v1/og", baseUrl);
    ogImageUrl.searchParams.set("title", title);
    ogImageUrl.searchParams.set("subtitle", subtitle);
  
    // Return the head section with metadata for SEO and social sharing
    return (
      <>
        <title>{title}</title>
        <meta content="width=device-width, initial-scale=1" name="viewport" />
        <meta name="description" content={subtitle} />
        <meta name="theme-color" content="#000000" />
        <meta name="title" content={title} />
        <meta name="keywords" content="Ciphare, secure file sharing, file encryption, privacy, security" />
        <meta name="language" content="English" />
        <meta name="revisit-after" content="7 days" />
        <meta name="robots" content="all" />
        <meta httpEquiv="Content-Type" content="text/html; charset=utf-8" />
        
        {/* Open Graph / Facebook */}
        <meta property="og:type" content="website" />
        <meta property="og:url" content={baseUrl} />
        <meta property="og:image" content={ogImageUrl.toString()} />
        <meta property="og:title" content={title} />
        <meta property="og:description" content={subtitle} />
        <meta property="og:image:width" content="1200" />
        <meta property="og:image:height" content="630" />
  
        {/* Twitter */}
        <meta property="twitter:card" content="summary_large_image" />
        <meta property="twitter:url" content={baseUrl} />
        <meta property="twitter:title" content={title} />
        <meta property="twitter:description" content={subtitle} />
        <meta property="twitter:image" content={ogImageUrl.toString()} />
      </>
    );
  }
  