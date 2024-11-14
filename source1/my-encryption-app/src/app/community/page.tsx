"use client";
import React, { useState, useEffect } from "react";
import { Title } from "../components/title";
import { ErrorMessage } from "../components/error";

// Define Post and Comment types
interface Comment {
  author: string;
  content: string;
}

// This is needed to define the Post type
interface Post {
  _id: string;
  title: string;
  content: string;
  author: string;
  likes: number;
  created_at: string;
  comments: Comment[];
}

export default function Community() {
  const [posts, setPosts] = useState<Post[]>([]);  // Initialize posts as an empty array
  const [title, setTitle] = useState("");  // Initialize title as an empty string
  const [content, setContent] = useState("");  // Initialize content as an empty string
  const [author, setAuthor] = useState("Anonymous");  // Initialize author as "Anonymous"
  const [ttl, setTtl] = useState(90); // Default to 3 months in days
  const [error, setError] = useState<string | null>(null);  // Initialize error as null

  useEffect(() => {
    fetchPosts();  // Fetch posts when the component is mounted
  }, []);

  const fetchPosts = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/v1/posts");  // Fetch posts from the API
      const result = await response.json();  // Parse the response as JSON
      setPosts(result);
    } catch (error) {
      setError("Failed to load posts.");
    }
  };

  const handleCreatePost = async () => {
    if (ttl < 1 || ttl > 90) {  // Validate TTL input (1 to 90 days) 
      setError("TTL must be between 1 and 90 days.");
      return;
    }
    setError(null); // Clear error message if TTL is valid

    try {
      const response = await fetch("http://localhost:5000/api/v1/posts", { // Create a new post using the API endpoint 
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

  const handleDeletePost = async (postId: string) => {  // Delete a post by ID
    await fetch(`http://localhost:5000/api/v1/posts/${postId}`, { method: "DELETE" });
    fetchPosts();
  };

  const handleLike = async (postId: string) => {  // Like a post by ID
    await fetch(`http://localhost:5000/api/v1/posts/${postId}/like`, { method: "POST" });
    fetchPosts();
  };

  const handleAddComment = async (postId: string, commentContent: string, commentAuthor: string) => {  // Add a comment to a post by ID
    await fetch(`http://localhost:5000/api/v1/posts/${postId}/comment`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: commentContent, author: commentAuthor }),
    });
    fetchPosts();
  };

  const handleDeleteComment = async (postId: string, commentIndex: number) => {  // Delete a comment by index
    await fetch(`http://localhost:5000/api/v1/posts/${postId}/comment/${commentIndex}`, { method: "DELETE" });
    fetchPosts();
  };

  return (  // Render the community posts page
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
          {posts.map((post) => (  // Render each post
            <div key={post._id} className="bg-zinc-800 p-4 mb-4 rounded">
              <h3 className="text-lg font-bold">{post.title}</h3>
              <p>{post.content}</p>
              <p className="text-sm text-zinc-400">by {post.author}</p>
              <p className="text-sm text-zinc-400">Likes: {post.likes}</p>
              <p className="text-sm text-zinc-400">Created at: {new Date(post.created_at).toLocaleString()}</p>
              <button onClick={() => handleLike(post._id)} className="mt-2 bg-blue-500 text-white rounded px-2">
                Like
              </button>
              <button onClick={() => handleDeletePost(post._id)} className="mt-2 bg-red-500 text-white rounded px-2 ml-2">
                Delete Post
              </button>

              {/* Render comments for the post */}
              <div className="mt-4">
                <h4 className="text-sm font-bold">Comments</h4>
                {Array.isArray(post.comments) ? (
                  post.comments.map((comment, idx) => (
                    <div key={idx} className="text-xs text-zinc-400">
                      - {comment.author}: {comment.content}
                      <button onClick={() => handleDeleteComment(post._id, idx)} className="text-red-500 ml-2">
                        Delete
                      </button>
                    </div>
                  ))
                ) : ( // Render a message if no comments are available
                  <p className="text-xs text-zinc-400">No comments available.</p>
                )}
                {/* Add a comment input */}
                <input 
                  type="text"
                  placeholder="Add a comment"
                  className="w-full p-2 mt-2 bg-zinc-900 border border-zinc-700 rounded text-zinc-300"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleAddComment(post._id, (e.target as HTMLInputElement).value, "Anonymous");
                      (e.target as HTMLInputElement).value = '';
                    }
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
