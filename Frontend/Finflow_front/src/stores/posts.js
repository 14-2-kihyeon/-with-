import { ref } from "vue"
import { defineStore } from "pinia"
import api from "@/api/axios"

export const usePostsStore = defineStore("posts", () => {
  const posts = ref([])
  const post = ref(null)

  const fetchPosts = async () => {
    const res = await api.get("/posts/")
    posts.value = res.data
  }

  const fetchPost = async (pk) => {
    const res = await api.get(`/posts/${pk}/`)
    post.value = res.data
    return res.data
  }

  const createPost = async (payload) => {
    const res = await api.post("/posts/", payload)
    return res.data
  }

  const updatePost = async (pk, payload) => {
    const res = await api.put(`/posts/${pk}/`, payload)
    return res.data
  }

  const deletePost = async (pk) => {
    await api.delete(`/posts/${pk}/`)
  }

  const createComment = async (pk, content) => {
    const res = await api.post(`/posts/${pk}/comments/`, { content })
    return res.data
  }

  const deleteComment = async (postPk, commentPk) => {
    await api.delete(`/posts/${postPk}/comments/${commentPk}/`)
  }

  return { posts, post, fetchPosts, fetchPost, createPost, updatePost, deletePost, createComment, deleteComment }
})
