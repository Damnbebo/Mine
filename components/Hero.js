import { useState, useEffect } from 'react'
import Image from 'next/image'
import styles from '../styles/components/Hero.module.css'

export default function Hero() {
  const [isLoaded, setIsLoaded] = useState(false)

  useEffect(() => {
    setIsLoaded(true)
  }, [])

  const scrollToBooking = () => {
    const element = document.getElementById('booking')
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <section id="home" className={styles.hero}>
      <div className={styles.heroBackground}>
        <Image
          src="https://images.pexels.com/photos/358070/pexels-photo-358070.jpeg"
          alt="Luxury car detailing"
          fill
          style={{ objectFit: 'cover' }}
          priority
          quality={90}
        />
        <div className={styles.overlay}></div>
      </div>

      <div className={styles.container}>
        <div className={styles.heroContent}>
          <div className={`${styles.heroText} ${isLoaded ? 'animate-fadeInUp' : ''}`}>
            <h1 className={styles.heroTitle}>
              GARDEN STATE
              <span className={styles.redText}> DETAILING</span>
            </h1>
            <p className={styles.heroSubtitle}>
              Hi, I'm Milton — a dedicated college student with a strong passion for automotive care. I take pride in delivering meticulous detailing services using premium products, all while providing exceptional customer service. Let me help restore your vehicle to its best condition.
            </p>
            <div className={styles.heroButtons}>
              <button onClick={scrollToBooking} className="btn-primary">
                Book Appointment
              </button>
              <button 
                onClick={() => document.getElementById('services').scrollIntoView({ behavior: 'smooth' })}
                className="btn-secondary"
              >
                Our Services
              </button>
            </div>
          </div>
        </div>

        <div className={styles.heroStats}>
          <div className={`${styles.stat} ${isLoaded ? 'animate-slideInLeft' : ''}`}>
            <h3>500+</h3>
            <p>Cars Detailed</p>
          </div>
          <div className={`${styles.stat} ${isLoaded ? 'animate-fadeInUp' : ''}`}>
            <h3>5 Years</h3>
            <p>Experience</p>
          </div>
          <div className={`${styles.stat} ${isLoaded ? 'animate-slideInRight' : ''}`}>
            <h3>100%</h3>
            <p>Satisfaction</p>
          </div>
        </div>
      </div>

      <div className={styles.scrollIndicator}>
        <div className={styles.scrollArrow}></div>
      </div>
    </section>
  )
}
