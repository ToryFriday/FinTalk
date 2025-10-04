import { useState, useEffect, useCallback } from 'react';
import BlogAPI from '../services/api';

/**
 * Custom hook for managing posts data with pagination support
 * Handles fetching, loading states, error handling, and pagination for posts
 */
const usePosts = (initialPage = 1, initialPageSize = 10) => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    currentPage: initialPage,
    pageSize: initialPageSize,
    totalPages: 0,
    totalPosts: 0,
    hasNext: false,
    hasPrevious: false,
    nextPage: null,
    previousPage: null
  });

  const fetchPosts = useCallback(async (page = pagination.currentPage, pageSize = pagination.pageSize) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await BlogAPI.getAllPosts({ page, page_size: pageSize });
      
      if (response.success) {
        // Handle paginated response from backend
        if (response.data && typeof response.data === 'object' && response.data.results) {
          // Paginated response
          const postsData = Array.isArray(response.data.results) ? response.data.results : [];
          setPosts(postsData);
          setPagination({
            currentPage: response.data.current_page || page,
            pageSize: response.data.page_size || pageSize,
            totalPages: response.data.total_pages || 0,
            totalPosts: response.data.count || 0,
            hasNext: !!response.data.next,
            hasPrevious: !!response.data.previous,
            nextPage: response.data.next,
            previousPage: response.data.previous
          });
          
          if (process.env.NODE_ENV === 'development') {
            console.log('usePosts - setting paginated posts:', postsData);
            console.log('usePosts - pagination info:', response.data);
          }
        } else {
          // Non-paginated response (fallback for mock data)
          const postsData = Array.isArray(response.data) ? response.data : [];
          setPosts(postsData);
          setPagination(prev => ({
            ...prev,
            totalPosts: postsData.length,
            totalPages: Math.ceil(postsData.length / pageSize)
          }));
          
          if (process.env.NODE_ENV === 'development') {
            console.log('usePosts - setting non-paginated posts:', postsData);
          }
        }
      } else {
        if (process.env.NODE_ENV === 'development') {
          console.log('usePosts - API error, setting empty array');
        }
        setError(response.error);
        setPosts([]); // Ensure posts is still an array on error
      }
    } catch (err) {
      if (process.env.NODE_ENV === 'development') {
        console.log('usePosts - catch block, setting empty array');
      }
      setError({
        type: 'UNKNOWN_ERROR',
        message: 'Failed to fetch posts',
        details: err
      });
      setPosts([]); // Ensure posts is still an array on error
    } finally {
      setLoading(false);
    }
  }, [pagination.currentPage, pagination.pageSize]);

  const refreshPosts = useCallback(() => {
    fetchPosts();
  }, [fetchPosts]);

  const goToPage = useCallback((page) => {
    if (page >= 1 && page <= pagination.totalPages) {
      fetchPosts(page, pagination.pageSize);
    }
  }, [fetchPosts, pagination.totalPages, pagination.pageSize]);

  const goToNextPage = useCallback(() => {
    if (pagination.hasNext) {
      goToPage(pagination.currentPage + 1);
    }
  }, [goToPage, pagination.hasNext, pagination.currentPage]);

  const goToPreviousPage = useCallback(() => {
    if (pagination.hasPrevious) {
      goToPage(pagination.currentPage - 1);
    }
  }, [goToPage, pagination.hasPrevious, pagination.currentPage]);

  const changePageSize = useCallback((newPageSize) => {
    fetchPosts(1, newPageSize); // Reset to first page when changing page size
  }, [fetchPosts]);

  const removePost = useCallback((postId) => {
    setPosts(prevPosts => {
      const newPosts = prevPosts.filter(post => post.id !== postId);
      // Update pagination count
      setPagination(prev => ({
        ...prev,
        totalPosts: Math.max(0, prev.totalPosts - 1),
        totalPages: Math.ceil(Math.max(0, prev.totalPosts - 1) / prev.pageSize)
      }));
      return newPosts;
    });
  }, []);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  return {
    posts,
    loading,
    error,
    pagination,
    refreshPosts,
    removePost,
    goToPage,
    goToNextPage,
    goToPreviousPage,
    changePageSize
  };
};

export default usePosts;