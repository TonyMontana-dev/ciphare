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
  ttl: number;
}

interface Post {
  _id: string;
  title: string;
  content: string;
  author: string;
  author_id: string; // Added unique ID for author
  likes: number;
  created_at: string;
  comments: Comment[];
}

export default function Community() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [author, setAuthor] = useState("Anonymous");
  const [ttl, setTtl] = useState(90); // Default TTL is 90 days
  const [error, setError] = useState<string | null>(null);
  const [visibleComments, setVisibleComments] = useState<Record<string, number>>({});

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000"; // Default to local server URL if not provided in environment variables

  // Memoize fetchPosts to prevent redefinition on every render
  const fetchPosts = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/posts`);
      if (!response.ok) throw new Error("Failed to fetch posts.");
      const result = await response.json();
      setPosts(result);
    } catch {
      setError("Failed to load posts.");
    }
  }, [API_BASE_URL]);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]); // Ensure useEffect runs only when fetchPosts changes

  const handleCreatePost = async () => {
    if (ttl < 1 || ttl > 90) {
      setError("TTL must be between 1 and 90 days.");
      return;
    }
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/posts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, content, author, ttl: ttl * 24 * 60 * 60 }),
      });

      if (response.ok) {
        setTitle("");
        setContent("");
        fetchPosts();
      }
    } catch {
      setError("Failed to create post.");
    }
  };

  const handleDeletePost = async (postId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/posts/${postId}`, {
        method: "DELETE",
      });

      if (response.ok) {
        setPosts((prevPosts) => prevPosts.filter((post) => post._id !== postId));
      }
    } catch {
      setError("An error occurred while deleting the post.");
    }
  };

  const handleLikePost = async (postId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/posts/${postId}/like`, {
        method: "POST",
      });

      if (response.ok) {
        fetchPosts();
      }
    } catch {
      setError("An error occurred while liking the post.");
    }
  };

  const handleAddComment = async (postId: string, commentContent: string) => {
    if (!commentContent) {
      setError("Comment content is required.");
      return;
    }
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/posts/${postId}/comment`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: commentContent,
          author: author,
          ttl: ttl * 24 * 60 * 60,
        }),
      });

      if (response.ok) {
        const updatedPost = await response.json();
        setPosts((prevPosts) =>
          prevPosts.map((post) => (post._id === postId ? updatedPost : post))
        );
      }
    } catch {
      setError("An unexpected error occurred.");
    }
  };

  const handleDeleteComment = async (postId: string, commentIndex: number) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/posts/${postId}/comment/${commentIndex}`,
        { method: "DELETE" }
      );

      if (response.ok) {
        fetchPosts();
      }
    } catch {
      setError("An error occurred while deleting the comment.");
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
            placeholder="Auto-destroy (days)"
            value={ttl}
            onChange={(e) => setTtl(parseInt(e.target.value))}
            className="w-full p-2 mb-4 bg-zinc-900 border border-zinc-700 rounded text-zinc-300"
          />
          <button onClick={handleCreatePost} className="w-full h-12 bg-zinc-200 text-zinc-900 rounded">
            Post
          </button>
        </div>

        <div className="mt-8">
          {posts.map((post) => (
            <div key={post._id} className="bg-zinc-800 p-4 mb-4 rounded">
              <h3 className="text-lg font-bold">{post.title}</h3>
              <p>{post.content}</p>
              <p className="text-sm text-zinc-400">
                by {post.author}#{post.author_id}
              </p>
              <p className="text-sm text-zinc-400">Likes: {post.likes}</p>
              <p className="text-sm text-zinc-400">Created at: {new Date(post.created_at).toLocaleString()}</p>
              <button
                onClick={() => handleLikePost(post._id)}
                className="mt-2 bg-blue-500 text-white rounded px-2"
              >
                Like
              </button>
              <button
                onClick={() => handleDeletePost(post._id)}
                className="mt-2 bg-red-500 text-white rounded px-2 ml-2"
              >
                Delete Post
              </button>

              <div className="mt-4">
                <h4 className="text-sm font-bold">Comments</h4>
                {post.comments.length > 0 ? (
                  <>
                    {post.comments.slice(0, visibleComments[post._id] || 2).map((comment, idx) => (
                      <div key={idx} className="text-xs text-zinc-400">
                        {comment.author}#{comment.author_id}: {comment.content} (Expires in{" "}
                        {Math.round(comment.ttl / (24 * 60 * 60))} days)
                        <button
                          onClick={() => handleDeleteComment(post._id, idx)}
                          className="text-red-500 ml-2"
                        >
                          Delete
                        </button>
                      </div>
                    ))}
                    {visibleComments[post._id] < post.comments.length && (
                      <button
                        onClick={() => handleLoadMoreComments(post._id)}
                        className="text-blue-500 mt-2" // Show "Load More" button
                      >
                        Load More Comments ({post.comments.length - (visibleComments[post._id] || 2)}) {/* Show remaining comments */}
                      </button>
                    )}
                  </>
                ) : (
                  <p className="text-xs text-zinc-400">No comments yet.</p>
                )}
                <input
                  type="text"
                  placeholder="Add a comment"
                  className="w-full p-2 mt-2 bg-zinc-900 border border-zinc-700 rounded text-zinc-300"
                  onKeyDown={(e) => e.key === "Enter" && handleAddComment(post._id, e.currentTarget.value)}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}