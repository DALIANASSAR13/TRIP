document.addEventListener('DOMContentLoaded', function() {
  // -----------------------------
  // Smooth Scroll for internal links
  // -----------------------------
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });

  // -----------------------------
  // Animate feature cards when they come into viewport
  // -----------------------------
  const featureCards = document.querySelectorAll('.feature-card');

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
      }
    });
  }, { threshold: 0.1 });

  featureCards.forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    observer.observe(card);
  });

  // -----------------------------
  // Toggle Sign In / Sign Up Modals
  // -----------------------------
  const signInModalEl = document.getElementById('signInModal');
  const signUpModalEl = document.getElementById('signUpModal');
  const goToSignUp = document.getElementById('goToSignUp');
  const goToSignIn = document.getElementById('goToSignIn');

  // Open Sign Up from Sign In
  if (goToSignUp && signInModalEl && signUpModalEl && window.bootstrap) {
    goToSignUp.addEventListener('click', function(e) {
      e.preventDefault();
      const signInModal = bootstrap.Modal.getInstance(signInModalEl) || new bootstrap.Modal(signInModalEl);
      const signUpModal = bootstrap.Modal.getInstance(signUpModalEl) || new bootstrap.Modal(signUpModalEl);
      signInModal.hide();
      signUpModal.show();
    });
  }

  // Open Sign In from Sign Up
  if (goToSignIn && signInModalEl && signUpModalEl && window.bootstrap) {
    goToSignIn.addEventListener('click', function(e) {
      e.preventDefault();
      const signInModal = bootstrap.Modal.getInstance(signInModalEl) || new bootstrap.Modal(signInModalEl);
      const signUpModal = bootstrap.Modal.getInstance(signUpModalEl) || new bootstrap.Modal(signUpModalEl);
      signUpModal.hide();
      signInModal.show();
    });
  }
});

// -----------------------------
// Change navbar background color on scroll
// -----------------------------
// Change navbar background color on scroll
window.addEventListener('scroll', function() {
  const navbar = document.querySelector('.navbar');
  if (!navbar) return;

  if (window.scrollY > 50) {
    navbar.style.backgroundColor = 'rgba(255, 255, 255, 0.25)';   // غامق
  } else {
    navbar.style.backgroundColor = 'rgba(255, 255, 255, 0.25)';   // غامق برضه
  }
});
