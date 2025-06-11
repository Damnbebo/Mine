import { useState, useEffect } from 'react'
import Image from 'next/image'
import styles from '../styles/components/Navbar.module.css'

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [slideUp, setSlideUp] = useState(false)
  const [lastScrollY, setLastScrollY] = useState(0)

  useEffect(() => {
    let timeoutId;
    
    const handleScroll = () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      timeoutId = setTimeout(() => {
        const currentScrollY = window.scrollY;
        setIsScrolled(currentScrollY > 20);

        if (currentScrollY > lastScrollY && currentScrollY > 200) {
          setSlideUp(true);
        } else if (currentScrollY < lastScrollY || currentScrollY < 100) {
          setSlideUp(false);
        }
        setLastScrollY(currentScrollY);
      }, 50);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', handleScroll);
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [lastScrollY]);

  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' })
      setIsMobileMenuOpen(false)
    }
  }

  return (
    <nav className={`${styles.navbar} ${isScrolled ? styles.scrolled : ''} ${slideUp ? styles['slide-up'] : ''}`}>
      <div className="container">
        <div className={`${styles.navContent} ${isMobileMenuOpen ? styles.menuOpen : ''}`}>
          <div className={`${styles.logo} ${slideUp ? styles.scaled : ''}`}>
            <Image
              src="/gardenbstate.png"
              alt="Garden State Detailing Logo"
              width={200}
              height={50}
              priority
            />
          </div>

          <div className={`${styles.navLinks} ${isMobileMenuOpen ? styles.mobileOpen : ''}`}>
            <button 
              onClick={() => scrollToSection('home')} 
              className={styles.navLink}
              style={{ '--index': 0 }}
            >
              Home
            </button>
            <button 
              onClick={() => scrollToSection('services')} 
              className={styles.navLink}
              style={{ '--index': 1 }}
            >
              Services
            </button>
            <button 
              onClick={() => scrollToSection('pricing')} 
              className={styles.navLink}
              style={{ '--index': 2 }}
            >
              Pricing
            </button>
            <button 
              onClick={() => scrollToSection('testimonials')} 
              className={styles.navLink}
              style={{ '--index': 3 }}
            >
              Testimonials
            </button>
            <button 
              onClick={() => scrollToSection('gallery')} 
              className={styles.navLink}
              style={{ '--index': 4 }}
            >
              Gallery
            </button>
            <button 
              onClick={() => scrollToSection('booking')} 
              className={`${styles.navLink} ${styles.bookingBtn}`}
              style={{ '--index': 5 }}
            >
              Book Now
            </button>
          </div>

          <button 
            className={styles.mobileToggle}
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            aria-label="Toggle mobile menu"
          >
            <span></span>
            <span></span>
            <span></span>
          </button>
        </div>
      </div>
    </nav>
  )
}
