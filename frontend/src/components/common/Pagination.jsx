import React, { memo, useMemo } from 'react';
import './Pagination.css';

/**
 * Pagination component for navigating through pages
 * Optimized with memoization for better performance
 * @param {Object} props - Component props
 * @param {number} props.currentPage - Current page number
 * @param {number} props.totalPages - Total number of pages
 * @param {number} props.totalItems - Total number of items
 * @param {number} props.pageSize - Items per page
 * @param {boolean} props.hasNext - Whether there's a next page
 * @param {boolean} props.hasPrevious - Whether there's a previous page
 * @param {Function} props.onPageChange - Handler for page changes
 * @param {Function} props.onPageSizeChange - Handler for page size changes
 * @param {Array} props.pageSizeOptions - Available page size options
 * @param {boolean} props.showPageSizeSelector - Whether to show page size selector
 * @param {boolean} props.showInfo - Whether to show pagination info
 */
const Pagination = memo(({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  hasNext,
  hasPrevious,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [5, 10, 20, 50],
  showPageSizeSelector = true,
  showInfo = true
}) => {
  // Calculate visible page numbers
  const visiblePages = useMemo(() => {
    const pages = [];
    const maxVisiblePages = 5;
    
    if (totalPages <= maxVisiblePages) {
      // Show all pages if total is small
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Show pages around current page
      const startPage = Math.max(1, currentPage - 2);
      const endPage = Math.min(totalPages, currentPage + 2);
      
      // Always show first page
      if (startPage > 1) {
        pages.push(1);
        if (startPage > 2) {
          pages.push('...');
        }
      }
      
      // Show pages around current
      for (let i = startPage; i <= endPage; i++) {
        pages.push(i);
      }
      
      // Always show last page
      if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
          pages.push('...');
        }
        pages.push(totalPages);
      }
    }
    
    return pages;
  }, [currentPage, totalPages]);

  // Calculate item range for current page
  const itemRange = useMemo(() => {
    const start = (currentPage - 1) * pageSize + 1;
    const end = Math.min(currentPage * pageSize, totalItems);
    return { start, end };
  }, [currentPage, pageSize, totalItems]);

  // Don't render if there's only one page or no items
  if (totalPages <= 1 && totalItems <= pageSize) {
    return null;
  }

  const handlePageClick = (page) => {
    if (page !== currentPage && page >= 1 && page <= totalPages) {
      onPageChange(page);
    }
  };

  const handlePageSizeChange = (event) => {
    const newPageSize = parseInt(event.target.value, 10);
    if (onPageSizeChange) {
      onPageSizeChange(newPageSize);
    }
  };

  return (
    <div className="pagination-container">
      {showInfo && (
        <div className="pagination-info">
          <span>
            Showing {itemRange.start}-{itemRange.end} of {totalItems} posts
          </span>
        </div>
      )}
      
      <div className="pagination-controls">
        {/* Previous button */}
        <button
          className={`pagination-button ${!hasPrevious ? 'disabled' : ''}`}
          onClick={() => handlePageClick(currentPage - 1)}
          disabled={!hasPrevious}
          type="button"
          aria-label="Go to previous page"
        >
          ← Previous
        </button>
        
        {/* Page numbers */}
        <div className="pagination-pages">
          {visiblePages.map((page, index) => (
            <button
              key={index}
              className={`pagination-page ${
                page === currentPage ? 'active' : ''
              } ${page === '...' ? 'ellipsis' : ''}`}
              onClick={() => page !== '...' && handlePageClick(page)}
              disabled={page === '...' || page === currentPage}
              type="button"
              aria-label={page === '...' ? 'More pages' : `Go to page ${page}`}
              aria-current={page === currentPage ? 'page' : undefined}
            >
              {page}
            </button>
          ))}
        </div>
        
        {/* Next button */}
        <button
          className={`pagination-button ${!hasNext ? 'disabled' : ''}`}
          onClick={() => handlePageClick(currentPage + 1)}
          disabled={!hasNext}
          type="button"
          aria-label="Go to next page"
        >
          Next →
        </button>
      </div>
      
      {showPageSizeSelector && (
        <div className="pagination-page-size">
          <label htmlFor="page-size-select">
            Posts per page:
            <select
              id="page-size-select"
              value={pageSize}
              onChange={handlePageSizeChange}
              className="page-size-select"
            >
              {pageSizeOptions.map(size => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </select>
          </label>
        </div>
      )}
    </div>
  );
});

// Display name for debugging
Pagination.displayName = 'Pagination';

export default Pagination;