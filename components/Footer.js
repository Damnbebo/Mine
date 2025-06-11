import styles from '../styles/components/Footer.module.css'

export default function Footer() {
  const currentYear = new Date().getFullYear()

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <footer className={styles.footer}>
      <div className="container">
        <div className={styles.footerContent}>
          <div className={styles.footerSection}>
            <div className={styles.logo}>
              <h3>LUXURY DETAILING</h3>
              <p>Premium automotive care for discerning clients. Experience the ultimate in vehicle detailing with our professional services.</p>
            </div>
            <div className={styles.socialLinks}>
              <a href="#" aria-label="Facebook" className={styles.socialLink}>
                <span>📘</span>
              </a>
              <a href="#" aria-label="Instagram" className={styles.socialLink}>
                <span>📷</span>
              </a>
              <a href="#" aria-label="Twitter" className={styles.socialLink}>
                <span>🐦</span>
              </a>
              <a href="#" aria-label="YouTube" className={styles.socialLink}>
                <span>📺</span>
              </a>
            </div>
          </div>

          <div className={styles.footerSection}>
            <h4>Quick Links</h4>
            <ul className={styles.footerLinks}>
              <li>
                <button onClick={() => scrollToSection('home')}>Home</button>
              </li>
              <li>
                <button onClick={() => scrollToSection('services')}>Services</button>
              </li>
              <li>
                <button onClick={() => scrollToSection('pricing')}>Pricing</button>
              </li>
              <li>
                <button onClick={() => scrollToSection('gallery')}>Gallery</button>
              </li>
              <li>
                <button onClick={() => scrollToSection('testimonials')}>Testimonials</button>
              </li>
              <li>
                <button onClick={() => scrollToSection('booking')}>Book Now</button>
              </li>
            </ul>
          </div>

          <div className={styles.footerSection}>
            <h4>Services</h4>
            <ul className={styles.footerLinks}>
              <li><a href="#">Exterior Detailing</a></li>
              <li><a href="#">Interior Detailing</a></li>
              <li><a href="#">Ceramic Coating</a></li>
              <li><a href="#">Paint Protection Film</a></li>
              <li><a href="#">Engine Bay Cleaning</a></li>
              <li><a href="#">Headlight Restoration</a></li>
            </ul>
          </div>

          <div className={styles.footerSection}>
            <h4>Contact Info</h4>
            <div className={styles.contactInfo}>
              <div className={styles.contactItem}>
                <span className={styles.contactIcon}>📍</span>
                <div>
                  <p>Wharton, NJ</p>
                </div>
              </div>
              <div className={styles.contactItem}>
                <span className={styles.contactIcon}>📞</span>
                <div>
                  <p>(973) 580-0014</p>
                </div>
              </div>
              <div className={styles.contactItem}>
                <span className={styles.contactIcon}>📧</span>
                <div>
                  <p>gardenstatedetailingllc@gmail.com</p>
                </div>
              </div>
              <div className={styles.contactItem}>
                <span className={styles.contactIcon}>🕒</span>
                <div>
                  <p>Mon-Sat: 9AM-3:30PM</p>
                </div>
              </div>
            </div>
          </div>
        </div>

          <div className={styles.footerBottom}>
            <div className={styles.footerBottomContent}>
              <div className={styles.copyright}>
                <p>&copy; {currentYear} Garden State Detailing. All rights reserved.</p>
              </div>
              <div className={styles.footerBottomLinks}>
                <a href="#">Privacy Policy</a>
                <a href="#">Terms of Service</a>
                <a href="#">Cookie Policy</a>
              </div>
              <button 
                className={styles.backToTop}
                onClick={scrollToTop}
                aria-label="Back to top"
              >
                <span>↑</span>
              </button>
            </div>
          </div>
      </div>

      <div className={styles.footerPattern}></div>
    </footer>
  )
}
