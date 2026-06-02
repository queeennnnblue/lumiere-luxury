// ============================================================
// LUMIÈRE — JavaScript Interactions
// ============================================================

// Modal Functions
function openModal(event) {
  const modal = document.getElementById('productModal');
  modal.classList.add('open');
}

function closeModal() {
  const modal = document.getElementById('productModal');
  modal.classList.remove('open');
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
  const modal = document.getElementById('productModal');
  const modalBox = document.querySelector('.modal-box');
  
  if (event.target === modal) {
    closeModal();
  }
});

// WhatsApp Button
function openWhatsApp() {
  const message = encodeURIComponent('السلام عليكم، أنا مهتم بطلب خاتم لوميير الذهبي. هل يمكنني معرفة المزيد؟');
  window.open(`https://wa.me/?text=${message}`, '_blank');
}

// Custom Order Form Submission
function submitCustomOrder(event) {
  event.preventDefault();
  
  const name = event.target.querySelector('input[type="text"]').value;
  const description = event.target.querySelector('textarea').value;
  const selectedMetal = document.querySelector('.opt.sel').textContent;
  
  // Show toast notification
  showToast('تم إرسال طلبك بنجاح! سنتواصل معك قريباً');
  
  // Reset form
  event.target.reset();
  
  // Log the order (in real app, this would be sent to a server)
  console.log({
    name,
    metal: selectedMetal,
    description,
    timestamp: new Date()
  });
}

// Toast Notification
function showToast(message) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.classList.add('show');
  
  setTimeout(() => {
    toast.classList.remove('show');
  }, 3000);
}

// Metal Selection Handler
document.addEventListener('DOMContentLoaded', function() {
  const opts = document.querySelectorAll('.opt');
  
  opts.forEach(opt => {
    opt.addEventListener('click', function() {
      // Remove previous selection
      document.querySelectorAll('.opt').forEach(o => o.classList.remove('sel'));
      // Add selection to clicked element
      this.classList.add('sel');
    });
  });

  // Filter functionality
  const chips = document.querySelectorAll('.chip');
  chips.forEach(chip => {
    chip.addEventListener('click', function() {
      // Remove active from all
      chips.forEach(c => c.classList.remove('active'));
      // Add active to clicked
      this.classList.add('active');
      
      // In a real app, this would filter products
      console.log('Filter selected:', this.textContent);
    });
  });

  // Language button
  const langBtn = document.querySelector('.lang-btn');
  if (langBtn) {
    langBtn.addEventListener('click', function() {
      alert('خاصية تغيير اللغة قادمة قريباً! 🚀');
    });
  }
});

// Smooth scroll enhancement
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function(e) {
    const href = this.getAttribute('href');
    if (href !== '#' && document.querySelector(href)) {
      e.preventDefault();
      // Small delay for better UX
      setTimeout(() => {
        document.querySelector(href).scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }, 100);
    }
  });
});
