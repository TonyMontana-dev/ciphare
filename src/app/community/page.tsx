"use client";
import React, { useState, useEffect, useCallback } from "react";
import { Title } from "../components/title";
import { ErrorMessage } from "../components/error";

// Define the types for Post and Comment
interface Comment {
  author: string;
  author_id: string; // Added unique ID for author
  content: string;
  timestamp: string;
  expires_in?: number; // Optional: days until expiration
}

interface Post {
  _id: string;
  title: string;
  content: string;
  author: string;
  author_id: string; // Added unique ID for author
  likes: number;
  created_at: string;
  expires_in?: number; // Optional: days until expiration
  comments: Comment[];
}

export default function Community() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [author, setAuthor] = useState("Anonymous");
  const [ttl, setTtl] = useState<number | "">(90); // Default TTL is 90 days
  const [error, setError] = useState<string | null>(null);
  const [visibleComments, setVisibleComments] = useState<Record<string, number>>({});
  const [commentTtls, setCommentTtls] = useState<Record<string, number | "">>({}); // TTL for each comment input

  // Use relative URLs in production, absolute URLs in development
  const API_BASE_URL = 
    typeof window !== 'undefined' && window.location.hostname === 'localhost'
      ? process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:3000"
      : ""; // Empty string means relative URLs

  // Memoize fetchPosts to prevent redefinition on every render
  const fetchPosts = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/posts`);
      if (!response.ok) {
        let errorMessage = "Failed to fetch posts.";
        try {
          const errorData = await response.json();
          if (errorData.error) {
            errorMessage = errorData.error;
          }
        } catch {
          errorMessage = response.statusText || errorMessage;
        }
        throw new Error(errorMessage);
      }
      const result = await response.json();
      console.log("Fetched Posts:", result); // Debugging: check the API response
      // Ensure result is an array to prevent crashes
      setPosts(Array.isArray(result) ? result : []);
      setError(null); // Clear any previous errors
    } catch (e) {
      const errorMsg = (e as Error).message;
      console.error("Error fetching posts:", errorMsg);
      setError(errorMsg);
    }
  }, [API_BASE_URL]);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]); // Ensure useEffect runs only when fetchPosts changes

  const handleCreatePost = async () => {
    if (!title.trim() || !content.trim()) {
      setError("Title and content are required.");
      return;
    }
    const ttlNum = typeof ttl === "number" ? ttl : (ttl === "" ? NaN : Number(ttl));
    if (isNaN(ttlNum) || ttlNum < 1 || ttlNum > 90) {
      setError("TTL is required and must be between 1 and 90 days.");
      return;
    }
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/posts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, content, author: author || "Anonymous", ttl: ttlNum * 24 * 60 * 60 }),
      });

      if (!response.ok) {
        let errorMessage = "Failed to create post.";
        try {
          const errorData = await response.json();
          if (errorData.error) {
            errorMessage = errorData.error;
          }
        } catch {
          errorMessage = response.statusText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      const result = await response.json();
      console.log("Post created:", result);
      setTitle("");
      setContent("");
      setError(null);
      fetchPosts(); // Refresh posts list
    } catch (e) {
      const errorMsg = (e as Error).message;
      console.error("Error creating post:", errorMsg);
      setError(errorMsg);
    }
  };

  const handleDeletePost = async (postId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/posts/${postId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        let errorMessage = "Failed to delete post.";
        try {
          const errorData = await response.json();
          if (errorData.error) {
            errorMessage = errorData.error;
          }
        } catch {
          errorMessage = response.statusText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      setPosts((prevPosts) => prevPosts.filter((post) => post._id !== postId));
      setError(null);
    } catch (e) {
      const errorMsg = (e as Error).message;
      console.error("Error deleting post:", errorMsg);
      setError(errorMsg);
    }
  };

  const handleLikePost = async (postId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/posts/${postId}/like`, {
        method: "POST",
      });

      if (!response.ok) {
        let errorMessage = "Failed to like post.";
        try {
          const errorData = await response.json();
          if (errorData.error) {
            errorMessage = errorData.error;
          }
        } catch {
          errorMessage = response.statusText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      // Refresh posts to show updated like count
      fetchPosts();
      setError(null);
    } catch (e) {
      const errorMsg = (e as Error).message;
      console.error("Error liking post:", errorMsg);
      setError(errorMsg);
    }
  };

  const handleAddComment = async (postId: string, commentContent: string, commentTtl?: number | "") => {
    if (!commentContent.trim()) {
      setError("Comment content is required.");
      return;
    }
    if (commentTtl === undefined || commentTtl === "") {
      setError("Comment TTL is required and must be between 1 and 90 days.");
      return;
    }
    const ttlNum = typeof commentTtl === "number" ? commentTtl : Number(commentTtl);
    if (isNaN(ttlNum) || ttlNum < 1 || ttlNum > 90) {
      setError("Comment TTL must be between 1 and 90 days.");
      return;
    }
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/posts/${postId}/comment`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: commentContent.trim(),
          author: author || "Anonymous",
          ttl: ttlNum * 24 * 60 * 60, // Convert days to seconds
        }),
      });

      if (!response.ok) {
        let errorMessage = "Failed to add comment.";
        try {
          const errorData = await response.json();
          if (errorData.error) {
            errorMessage = errorData.error;
          }
        } catch {
          errorMessage = response.statusText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      // Refresh posts to show new comment
      fetchPosts();
      setError(null);
    } catch (e) {
      const errorMsg = (e as Error).message;
      console.error("Error adding comment:", errorMsg);
      setError(errorMsg);
    }
  };

  const handleDeleteComment = async (postId: string, commentId: string) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/posts/${postId}/comment/${commentId}`,
        { method: "DELETE" }
      );

      if (!response.ok) {
        let errorMessage = "Failed to delete comment.";
        try {
          const errorData = await response.json();
          if (errorData.error) {
            errorMessage = errorData.error;
          }
        } catch {
          errorMessage = response.statusText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      // Refresh posts to reflect deleted comment
      fetchPosts();
      setError(null);
    } catch (e) {
      const errorMsg = (e as Error).message;
      console.error("Error deleting comment:", errorMsg);
      setError(errorMsg);
    }
  };

  const handleLoadMoreComments = (postId: string) => {
    setVisibleComments((prev) => ({
      ...prev,
      [postId]: (prev[postId] || 2) + 2,
    }));
  };

  return (
    <div className="container px-8 mx-auto mt-16 lg:mt-32">
      {error && <ErrorMessage message={error} />}
      <div className="max-w-3xl mx-auto">
        <Title>Community Posts</Title>
        <div className="mt-8">
          <input
            type="text"
            placeholder="Post Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full p-2 mb-2 bg-zinc-900 border border-zinc-700 rounded text-zinc-300"
          />
          <textarea
            placeholder="Post Content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="w-full p-2 mb-2 bg-zinc-900 border border-zinc-700 rounded text-zinc-300"
          />
          <input
            type="text"
            placeholder="Your Name (or Anonymous)"
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            className="w-full p-2 mb-2 bg-zinc-900 border border-zinc-700 rounded text-zinc-300"
          />
          <input
            type="number"
            placeholder="Auto-destroy (days) - Required: 1-90"
            value={ttl}
            min={1}
            max={90}
            required
            onChange={(e) => {
              const value = e.target.value === "" ? "" : (isNaN(parseInt(e.target.value)) ? "" : parseInt(e.target.value));
              setTtl(value);
            }}
            className="w-full p-2 mb-4 bg-zinc-900 border border-zinc-700 rounded text-zinc-300"
          />
          {ttl === "" && (
            <p className="text-red-400 text-sm mb-2">TTL is required (1-90 days)</p>
          )}
          {typeof ttl === "number" && (ttl < 1 || ttl > 90) && (
            <p className="text-red-400 text-sm mb-2">TTL must be between 1 and 90 days</p>
          )}
          <button onClick={handleCreatePost} className="w-full h-12 bg-zinc-200 text-zinc-900 rounded">
            Post
          </button>
        </div>

        <div className="mt-8">
          {posts.map((post) => {
            // Safety check - skip if post is invalid
            if (!post || !post._id) return null;
            const comments = Array.isArray(post.comments) ? post.comments : [];
            return (
            <div key={post._id} className="bg-zinc-800 p-4 mb-4 rounded">
              <h3 className="text-lg font-bold">{post.title}</h3>
              <p>{post.content}</p>
              <p className="text-sm text-zinc-400">
                by {post.author}#{post.author_id}
              </p>
              <div className="flex items-center gap-4 mt-2">
                <span className="text-sm text-zinc-400">Likes: {post.likes}</span>
                <span className="text-sm text-zinc-400">Created: {post.created_at ? new Date(post.created_at).toLocaleString() : 'Unknown'}</span>
                {post.expires_in !== undefined && (
                  <span className="text-sm text-zinc-500">Expires in: {post.expires_in} days</span>
                )}
              </div>
              <div className="flex gap-2 mt-2">
                <button
                  onClick={() => handleLikePost(post._id)}
                  className="bg-blue-500 hover:bg-blue-600 text-white rounded px-4 py-1 text-sm"
                >
                  👍 Like
                </button>
                <button
                  onClick={() => handleDeletePost(post._id)}
                  className="bg-red-500 hover:bg-red-600 text-white rounded px-4 py-1 text-sm"
                >
                  🗑️ Delete
                </button>
              </div>

              <div className="mt-4">
                <h4 className="text-sm font-bold">Comments</h4>
                {comments.length > 0 ? (
                  <>
                    {comments.slice(0, visibleComments[post._id] || 2).map((comment) => {
                      if (!comment || !comment.author_id) return null;
                      return (
                      <div key={`${post._id}-${comment.author_id}-${comment.timestamp}`} className="text-sm text-zinc-300 mb-3 p-3 bg-zinc-900 rounded border border-zinc-700">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="font-semibold text-zinc-200 mb-1">{comment.author}</div>
                            <div className="text-zinc-300 mb-2">{comment.content}</div>
                            <div className="text-zinc-500 text-xs">
                              {comment.timestamp ? new Date(comment.timestamp).toLocaleString() : 'Unknown'}
                              {comment.expires_in !== undefined && (
                                <span className="ml-2">• Expires in {comment.expires_in} days</span>
                              )}
                            </div>
                          </div>
                          <button
                            onClick={() => handleDeleteComment(post._id, comment.author_id)}
                            className="text-red-500 hover:text-red-400 text-xs px-2 py-1 hover:bg-red-500/10 rounded"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                      );
                    })}
                    {comments.length > (visibleComments[post._id] || 2) && (
                      <button
                        onClick={() => handleLoadMoreComments(post._id)}
                        className="text-blue-500 hover:text-blue-400 mt-2 text-sm"
                      >
                        Load More Comments ({comments.length - (visibleComments[post._id] || 2)} remaining)
                      </button>
                    )}
                  </>
                ) : (
                  <p className="text-xs text-zinc-400">No comments yet.</p>
                )}
                <div className="mt-2 space-y-2">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="Add a comment..."
                      id={`comment-input-${post._id}`}
                      className="flex-1 p-2 bg-zinc-900 border border-zinc-700 rounded text-zinc-300"
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          const input = e.currentTarget;
                          const ttlInput = document.getElementById(`comment-ttl-${post._id}`) as HTMLInputElement;
                          if (input.value.trim() && ttlInput && ttlInput.value) {
                            const ttlValue = parseInt(ttlInput.value);
                            if (!isNaN(ttlValue)) {
                              handleAddComment(post._id, input.value, ttlValue);
                              input.value = "";
                              ttlInput.value = "";
                              setCommentTtls(prev => ({ ...prev, [post._id]: "" }));
                            }
                          }
                        }
                      }}
                    />
                    <input
                      type="number"
                      id={`comment-ttl-${post._id}`}
                      placeholder="TTL (days)"
                      min={1}
                      max={90}
                      required
                      value={commentTtls[post._id] || ""}
                      onChange={(e) => {
                        const value = e.target.value === "" ? "" : parseInt(e.target.value);
                        setCommentTtls(prev => ({ ...prev, [post._id]: value }));
                      }}
                      className="w-24 p-2 bg-zinc-900 border border-zinc-700 rounded text-zinc-300"
                    />
                    <button
                      onClick={() => {
                        const input = document.getElementById(`comment-input-${post._id}`) as HTMLInputElement;
                        const ttlInput = document.getElementById(`comment-ttl-${post._id}`) as HTMLInputElement;
                        if (input && input.value.trim() && ttlInput && ttlInput.value) {
                          const ttlValue = parseInt(ttlInput.value);
                          if (!isNaN(ttlValue)) {
                            handleAddComment(post._id, input.value, ttlValue);
                          }
                          input.value = "";
                          ttlInput.value = "";
                          setCommentTtls(prev => ({ ...prev, [post._id]: "" }));
                        }
                      }}
                      className="bg-zinc-700 hover:bg-zinc-600 text-zinc-300 rounded px-4 py-2"
                    >
                      Post
                    </button>
                  </div>
                  {(() => {
                    const commentTtl = commentTtls[post._id];
                    if (commentTtl === "" || commentTtl === undefined) {
                      return <p className="text-red-400 text-xs">Comment TTL is required (1-90 days)</p>;
                    }
                    if (typeof commentTtl === "number" && (commentTtl < 1 || commentTtl > 90)) {
                      return <p className="text-red-400 text-xs">Comment TTL must be between 1 and 90 days</p>;
                    }
                    return null;
                  })()}
                </div>
              </div>
            </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}