"use client";
import React, { useState, useEffect, useCallback } from "react";
import { Title } from "../components/title";
import { ErrorMessage } from "../components/error";

// Define the types for Post and Comment
interface Comment {
  id: string;
  content: string;
  author: string;
  created_at: string;
  ttl?: number;
  expires_at?: string;
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
  ttl: number;
  dislikes: number;
  expires_in: number;
}

export default function Community() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [author, setAuthor] = useState("Anonymous");
  const [ttl, setTtl] = useState(1);
  const [ttlMultiplier, setTtlMultiplier] = useState(86400); // Default to days
  const [commentTtl, setCommentTtl] = useState(1);
  const [commentTtlMultiplier, setCommentTtlMultiplier] = useState(3600); // Default to hours
  const [error, setError] = useState<string | null>(null);
  const [visiblePosts, setVisiblePosts] = useState(10); // Show first 10 posts initially
  const [visibleComments, setVisibleComments] = useState<Record<string, number>>({});

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:3000"; // Default to local server URL if not provided in environment variables

  // Memoize fetchPosts to prevent redefinition on every render
  const fetchPosts = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/posts`);
      if (!response.ok) throw new Error("Failed to fetch posts.");
      const result = await response.json();
      console.log("Fetched Posts:", result); // Debugging: check the API response
      setPosts(result);
    } catch {
      console.error("Error fetching posts:", error); // Log any errors
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
      // Ensure TTL is a proper integer
      const ttlValue = parseInt(ttl.toString()) * parseInt(ttlMultiplier.toString());
      const response = await fetch(`${API_BASE_URL}/api/posts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          title, 
          content, 
          author, 
          ttl: ttlValue
        }),
      });

      if (response.ok) {
        setTitle("");
        setContent("");
        fetchPosts();
      } else {
        const errorData = await response.json();
        setError(errorData.error || "Failed to create post");
      }
    } catch {
      setError("Failed to create post.");
    }
  };

  const handleDeletePost = async (postId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/posts/${postId}`, {
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
      const response = await fetch(`${API_BASE_URL}/api/posts/${postId}/reaction`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "like" }),
      });

      if (response.ok) {
        fetchPosts(); // Refresh posts to get updated reactions
      }
    } catch {
      setError("Failed to update post reaction");
    }
  };

  const handleDislikePost = async (postId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/posts/${postId}/reaction`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "dislike" }),
      });

      if (response.ok) {
        fetchPosts(); // Refresh posts to get updated reactions
      }
    } catch {
      setError("Failed to update post reaction");
    }
  };

  const handleAddComment = async (postId: string, commentContent: string) => {
    if (!commentContent) {
      setError("Comment content is required.");
      return;
    }
    setError(null);

    try {
      // Debug log the initial values
      console.log("Initial commentTtl:", commentTtl, "Type:", typeof commentTtl);
      console.log("Initial commentTtlMultiplier:", commentTtlMultiplier, "Type:", typeof commentTtlMultiplier);

      // Force integer conversion with multiple checks
      const ttlNum = Math.floor(Number(commentTtl));
      const multiplierNum = Math.floor(Number(commentTtlMultiplier));
      
      console.log("After Number conversion - ttlNum:", ttlNum, "Type:", typeof ttlNum);
      console.log("After Number conversion - multiplierNum:", multiplierNum, "Type:", typeof multiplierNum);

      if (isNaN(ttlNum) || isNaN(multiplierNum)) {
        setError("Invalid TTL values");
        return;
      }

      // Calculate TTL in seconds
      const ttlValue = Math.floor(ttlNum * multiplierNum);
      console.log("Final TTL value:", ttlValue, "Type:", typeof ttlValue);
      
      // Verify it's an integer
      if (!Number.isInteger(ttlValue)) {
        console.error("TTL is not an integer!");
        setError("Invalid TTL calculation");
        return;
      }

      const requestBody = {
        content: commentContent,
        author: author,
        ttl: ttlValue
      };
      
      console.log("Request body:", JSON.stringify(requestBody, null, 2));
      
      const response = await fetch(`${API_BASE_URL}/api/posts/${postId}/comments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      if (response.ok) {
        fetchPosts(); // Refresh posts to get updated comments
      } else {
        const errorData = await response.json();
        console.error("Server error response:", {
          status: response.status,
          statusText: response.statusText,
          data: errorData
        });
        setError(errorData.error || `Failed to add comment (Status: ${response.status})`);
      }
    } catch (error) {
      console.error("Error in handleAddComment:", error);
      setError(`An unexpected error occurred: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  const handleDeleteComment = async (postId: string, commentId: string) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/posts/${postId}/comments/${commentId}`,
        { method: "DELETE" }
      );

      if (response.ok) {
        fetchPosts(); // Refresh posts to get updated comments
      }
    } catch {
      setError("An error occurred while deleting the comment.");
    }
  };

  const handleLoadMorePosts = () => {
    setVisiblePosts(prev => prev + 10);
  };

  const handleLoadMoreComments = (postId: string) => {
    setVisibleComments(prev => ({
      ...prev,
      [postId]: (prev[postId] || 5) + 5 // Show 5 more comments at a time
    }));
  };

  return (
    <div className="container px-8 mx-auto mt-16 lg:mt-32 bg-gradient-to-b from-gray-900 to-gray-800 rounded-lg shadow-xl p-8">
      {error && <ErrorMessage message={error} />}
      <div className="max-w-3xl mx-auto">
        <Title>Community Posts</Title>
        
        {/* Post Creation Form */}
        <div className="bg-gray-800 rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4 text-white">Create a New Post</h2>
          <div className="space-y-4">
            <input
              type="text"
              placeholder="Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full p-2 border rounded bg-gray-700 text-white border-gray-600 placeholder-gray-400"
            />
            <textarea
              placeholder="Content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="w-full p-2 border rounded h-32 bg-gray-700 text-white border-gray-600 placeholder-gray-400"
            />
            <div className="flex items-center space-x-4">
              <input
                type="text"
                placeholder="Author"
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
                className="flex-1 p-2 border rounded bg-gray-700 text-white border-gray-600 placeholder-gray-400"
              />
              <div className="flex items-center space-x-2">
                <input
                  type="number"
                  value={ttl}
                  onChange={(e) => setTtl(Number(e.target.value))}
                  min="1"
                  max="90"
                  className="w-20 p-2 border rounded bg-gray-700 text-white border-gray-600"
                />
                <select
                  value={ttlMultiplier}
                  onChange={(e) => setTtlMultiplier(Number(e.target.value))}
                  className="p-2 border rounded bg-gray-700 text-white border-gray-600"
                >
                  <option value={86400}>Days</option>
                  <option value={3600}>Hours</option>
                  <option value={60}>Minutes</option>
                </select>
              </div>
            </div>
            <button
              onClick={handleCreatePost}
              className="w-full bg-gray-700 text-white py-2 rounded hover:bg-gray-600 transition-colors"
            >
              Create Post
            </button>
          </div>
        </div>

        {/* Posts List */}
        <div className="space-y-6">
          {posts.slice(0, visiblePosts).map((post) => (
            <div key={post._id} className="bg-gray-800 rounded-lg shadow-md p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-white">{post.title}</h3>
                  <p className="text-gray-300">
                    By {post.author} #{post.author_id.slice(0, 8)}
                  </p>
                  <p className="text-sm text-gray-400">
                    Posted {new Date(post.created_at).toLocaleString()}
                  </p>
                  <p className="text-sm text-gray-400">
                    Expires in {post.expires_in} days
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleLikePost(post._id)}
                    className="text-gray-300 hover:text-white transition-colors"
                  >
                    👍 {post.likes}
                  </button>
                  <button
                    onClick={() => handleDislikePost(post._id)}
                    className="text-gray-300 hover:text-white transition-colors"
                  >
                    👎 {post.dislikes}
                  </button>
                </div>
              </div>
              <p className="text-gray-300 mb-4">{post.content}</p>

              {/* Comments Section */}
              <div className="mt-6 border-t border-gray-700 pt-4">
                <h4 className="text-lg font-semibold mb-4 text-white">Comments</h4>
                <div className="space-y-4">
                  {post.comments.slice(0, visibleComments[post._id] || 5).map((comment) => (
                    <div key={comment.id} className="bg-gray-700 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium text-white">
                            {comment.author} #{comment.id.slice(0, 8)}
                          </p>
                          <p className="text-sm text-gray-400">
                            {new Date(comment.created_at).toLocaleString()}
                          </p>
                          {comment.expires_at && (
                            <p className="text-sm text-gray-400">
                              Expires: {new Date(comment.expires_at).toLocaleString()}
                            </p>
                          )}
                        </div>
                      </div>
                      <p className="mt-2 text-gray-300">{comment.content}</p>
                    </div>
                  ))}
                  {post.comments.length > (visibleComments[post._id] || 5) && (
                    <button
                      onClick={() => handleLoadMoreComments(post._id)}
                      className="text-gray-300 hover:text-white transition-colors"
                    >
                      Load More Comments
                    </button>
                  )}
                </div>

                {/* Comment Form */}
                <div className="mt-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <input
                      type="number"
                      value={commentTtl}
                      onChange={(e) => setCommentTtl(Number(e.target.value))}
                      min="1"
                      className="w-20 p-2 border rounded bg-gray-700 text-white border-gray-600"
                    />
                    <select
                      value={commentTtlMultiplier}
                      onChange={(e) => setCommentTtlMultiplier(Number(e.target.value))}
                      className="p-2 border rounded bg-gray-700 text-white border-gray-600"
                    >
                      <option value={3600}>Hours</option>
                      <option value={60}>Minutes</option>
                    </select>
                  </div>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      placeholder="Add a comment..."
                      className="flex-1 p-2 border rounded bg-gray-700 text-white border-gray-600 placeholder-gray-400"
                      onKeyPress={(e) => {
                        if (e.key === "Enter") {
                          handleAddComment(post._id, e.currentTarget.value);
                          e.currentTarget.value = "";
                        }
                      }}
                    />
                    <button
                      onClick={() => {
                        const input = document.querySelector(`input[placeholder="Add a comment..."]`) as HTMLInputElement;
                        if (input) {
                          handleAddComment(post._id, input.value);
                          input.value = "";
                        }
                      }}
                      className="bg-gray-700 text-white px-4 py-2 rounded hover:bg-gray-600 transition-colors"
                    >
                      Comment
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
          {posts.length > visiblePosts && (
            <button
              onClick={handleLoadMorePosts}
              className="w-full bg-gray-700 text-white py-2 rounded hover:bg-gray-600 transition-colors"
            >
              Load More Posts
            </button>
          )}
        </div>
      </div>
    </div>
  );
}