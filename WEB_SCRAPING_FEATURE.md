# ✅ Web Scraping Feature for RAG

## Overview

Added web scraping capability to the VC Best Practices section, allowing users to provide website URLs that the AI can search and extract content from.

## What Was Implemented

### 1. Web Scraping in Document Ingestion Service

**New Methods**:
- `ingest_url(url)` - Scrape and ingest content from a single URL
- `ingest_urls(urls)` - Scrape and ingest content from multiple URLs
- `_is_valid_url(url)` - Validate URL format

**Features**:
- **HTML Parsing**: Uses BeautifulSoup to extract text content
- **Content Cleaning**: Removes scripts, styles, nav, footer, header
- **Text Extraction**: Extracts clean text content
- **Title Extraction**: Captures page title if available
- **Metadata Tracking**: Stores URL, domain, title in metadata
- **Error Handling**: Graceful handling of network errors, invalid URLs

### 2. Enhanced UI with Tabs

**New Tab Structure**:
- **Tab 1: Upload Files** - Existing file upload functionality
- **Tab 2: Add Websites** - New URL input functionality

**URL Input Features**:
- Text input for URL
- URL validation
- Scraping button with progress indicator
- List of ingested URLs
- Clear URLs button
- Unified document summary (files + websites)

### 3. Integration

- URLs are processed through the same document ingestion pipeline
- Content is chunked using the same strategy as files
- Chunks are added to the same document store
- RAG retrieval works seamlessly with both files and URLs

## Usage

### Step 1: Add Website
1. Go to "📚 VC Best Practices & Documentation" section
2. Click on "🌐 Add Websites" tab
3. Enter a website URL (e.g., `https://example.com/article`)
4. Click "🔍 Scrape & Add Website"
5. Wait for content extraction (usually 2-5 seconds)

### Step 2: Verify Content
- Check "Current Knowledge Base" section
- See website listed with chunk count
- Website icon (🌐) distinguishes from files (📄)

### Step 3: Use in Analysis
- URLs are automatically used in RAG retrieval
- Content is searched based on investment criteria
- Relevant chunks are injected into analysis prompts

## Technical Details

### Web Scraping Process

```
URL Input → HTTP Request → HTML Parsing → Text Extraction → Chunking → Embedding → Storage
```

**Steps**:
1. **HTTP Request**: Fetches page with proper User-Agent header
2. **HTML Parsing**: BeautifulSoup parses HTML structure
3. **Content Cleaning**: Removes non-content elements (scripts, styles, nav, footer, header)
4. **Text Extraction**: Gets clean text content
5. **Chunking**: Same paragraph-aware chunking as files
6. **Metadata**: Extracts title, domain, URL
7. **Embedding**: Generates embeddings for chunks
8. **Storage**: Adds to document store

### Supported URLs

**Works Well With**:
- Static HTML pages
- Articles and blog posts
- Documentation pages
- Wiki pages (if publicly accessible)
- News articles
- Research papers (HTML format)

**May Have Issues With**:
- JavaScript-rendered content (requires headless browser)
- Pages requiring authentication
- Paywalled content
- Very large pages (may timeout)
- Rate-limited sites

### Content Extraction Quality

**What Gets Extracted**:
- Main article/content text
- Headings and subheadings
- Paragraphs and body text
- Lists and structured content

**What Gets Filtered**:
- Navigation menus
- Footers and headers
- Sidebars and ads
- Script and style tags
- Comments and metadata

## Example Use Cases

### 1. Industry Research
```
URL: https://techcrunch.com/2024/01/ai-investment-trends
→ Extract latest AI investment trends and insights
```

### 2. Best Practices Articles
```
URL: https://firstround.com/review/best-practices-for-series-a
→ Extract Series A investment best practices
```

### 3. Internal Wiki
```
URL: https://your-company-wiki.com/investment-criteria
→ Extract internal investment criteria and guidelines
```

### 4. Sector Reports
```
URL: https://marketresearch.com/saas-2024-report
→ Extract sector-specific insights and benchmarks
```

## Error Handling

### Common Errors

1. **Invalid URL**
   - Error: "Invalid URL format"
   - Solution: Ensure URL starts with http:// or https://

2. **Network Error**
   - Error: "Failed to fetch URL"
   - Solution: Check internet connection, verify URL is accessible

3. **Timeout**
   - Error: Request timeout
   - Solution: Large pages may timeout, try smaller pages

4. **Access Denied**
   - Error: 403 Forbidden
   - Solution: Page may require authentication or block scrapers

5. **No Content**
   - Warning: "No content extracted"
   - Solution: Page may be empty, require JavaScript, or be blocked

## Dependencies

**Required Packages**:
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `lxml` - Fast HTML parser (optional but recommended)

**Installation**:
```bash
pip install requests beautifulsoup4 lxml
```

## Limitations & Future Enhancements

### Current Limitations:
- **Static HTML Only**: Doesn't handle JavaScript-rendered content
- **Single Page**: Scrapes only the provided URL (not linked pages)
- **No Authentication**: Can't access password-protected content
- **Basic Parsing**: Uses simple HTML parsing (not specialized extractors)

### Future Enhancements:
1. **JavaScript Support**: Use Selenium/Playwright for JS-rendered pages
2. **Sitemap Crawling**: Crawl entire websites from sitemap
3. **Authentication**: Support for authenticated pages
4. **Specialized Extractors**: Use tools like Readability, Trafilatura
5. **PDF from URLs**: Extract PDFs linked from URLs
6. **Recursive Crawling**: Follow links to related pages
7. **Content Filtering**: Smart filtering of relevant vs irrelevant content
8. **Rate Limiting**: Respect robots.txt and rate limits

## Best Practices

### For Users:
1. **Use Specific URLs**: Link to specific articles/pages, not homepages
2. **Check Accessibility**: Ensure URLs are publicly accessible
3. **Verify Content**: Check that extracted content looks correct
4. **Combine Sources**: Use both files and URLs for comprehensive coverage

### For Developers:
1. **Respect robots.txt**: Consider implementing robots.txt checking
2. **Rate Limiting**: Add delays between requests if scraping multiple URLs
3. **User-Agent**: Use proper User-Agent headers (already implemented)
4. **Error Handling**: Handle network errors gracefully (already implemented)
5. **Content Validation**: Validate extracted content quality

---

**Status**: ✅ Complete and Ready to Use!

**Impact**: Enables ingestion of external resources, articles, and web-based documentation into the RAG system, significantly expanding the knowledge base capabilities.
