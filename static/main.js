// Load posts on page start
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('posts-container')) {
    loadPosts('all');
  }
});

let currentCategory = 'all';

// Fetch posts from REST API and render them
async function loadPosts(category) {
  currentCategory = category;
  const container = document.getElementById('posts-container');
  container.innerHTML = '<p class="empty-msg">Loading...</p>';

  const res = await fetch(`/api/posts?category=${category}`);
  const posts = await res.json();

  if (posts.length === 0) {
    container.innerHTML = '<p class="empty-msg">No notices yet. Post one!</p>';
    return;
  }

  container.innerHTML = posts.map(post => `
    <div class="post-card" id="post-${post.id}">
      <div class="post-header">
        <div>
          <span class="post-category">${post.category}</span>
          <h3 class="post-title">${post.title}</h3>
        </div>
        <button
          class="upvote-btn ${post.upvoted_by_me ? 'upvoted' : ''}"
          onclick="upvote(${post.id})">
          ▲ <span id="upvote-count-${post.id}">${post.upvotes}</span>
        </button>
      </div>
      <p class="post-body">${post.body}</p>
      <div class="post-footer">
        <span>By ${post.author} · ${post.created_at}</span>
        ${post.is_mine ? `
          <button class="delete-btn" onclick="deletePost(${post.id})">✕ Delete</button>
        ` : ''}
      </div>
    </div>
  `).join('');
}

// Create a new post
async function createPost() {
  const title = document.getElementById('title').value.trim();
  const body = document.getElementById('body').value.trim();
  const category = document.getElementById('category').value;

  if (!title || !body) {
    alert('Title and body are required.');
    return;
  }

  const res = await fetch('/api/posts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, body, category })
  });

  if (res.ok) {
    document.getElementById('title').value = '';
    document.getElementById('body').value = '';
    loadPosts(currentCategory);
  }
}

// Upvote a post
async function upvote(id) {
  const res = await fetch(`/api/posts/${id}/upvote`, { method: 'POST' });
  const data = await res.json();

  const btn = document.querySelector(`#post-${id} .upvote-btn`);
  const count = document.getElementById(`upvote-count-${id}`);
  count.textContent = data.upvotes;
  btn.classList.toggle('upvoted');
}

// Delete a post
async function deletePost(id) {
  if (!confirm('Delete this notice?')) return;

  const res = await fetch(`/api/posts/${id}`, { method: 'DELETE' });
  if (res.ok) {
    document.getElementById(`post-${id}`).remove();
  } else {
    alert('Delete failed: ' + res.status);
  }
}

// Filter posts by category
function filterPosts(category, btn) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  loadPosts(category);
}