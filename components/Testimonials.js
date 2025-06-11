import { useState, useEffect } from 'react'
import styles from '../styles/components/Testimonials.module.css'

export default function Testimonials() {
  const [isVisible, setIsVisible] = useState(false)
  const [currentSlide, setCurrentSlide] = useState(0)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true)
        }
      },
      { threshold: 0.1 }
    )

    const element = document.getElementById('testimonials')
    if (element) {
      observer.observe(element)
    }

    return () => {
      if (element) {
        observer.unobserve(element)
      }
    }
  }, [])

  const testimonials = [
    {
      name: "Michael Rodriguez",
      title: "Ferrari 488 Owner",
      image: "https://images.pexels.com/photos/2379004/pexels-photo-2379004.jpeg",
      rating: 5,
      text: "Absolutely exceptional service! My Ferrari has never looked better. The attention to detail and professionalism exceeded all my expectations. The ceramic coating they applied has kept my car looking showroom fresh for months."
    },
    {
      name: "Sarah Chen",
      title: "Porsche 911 Owner",
      image: "https://images.pexels.com/photos/1239291/pexels-photo-1239291.jpeg",
      rating: 5,
      text: "I've tried many detailing services, but none compare to this level of excellence. They treated my Porsche like their own and the results speak for themselves. The paint correction work was flawless."
    },
    {
      name: "David Thompson",
      title: "Lamborghini Huracán Owner",
      image: "https://images.pexels.com/photos/1222271/pexels-photo-1222271.jpeg",
      rating: 5,
      text: "Outstanding work on my Lamborghini! The team's expertise with luxury vehicles is evident in every detail. The paint protection film installation was perfect, and the customer service was top-notch throughout the entire process."
    },
    {
      name: "Jennifer Walsh",
      title: "Mercedes S-Class Owner",
      image: "https://images.pexels.com/photos/1181686/pexels-photo-1181686.jpeg",
      rating: 5,
      text: "Professional, reliable, and incredibly skilled. They transformed my Mercedes both inside and out. The leather conditioning brought my seats back to life, and the exterior finish is absolutely stunning."
    },
    {
      name: "Robert Kim",
      title: "BMW M5 Owner",
      image: "https://images.pexels.com/photos/1043471/pexels-photo-1043471.jpeg",
      rating: 5,
      text: "The best investment I've made for my BMW. The comprehensive detailing package was worth every penny. My car looks better than when I first bought it, and the protective coatings have maintained that finish beautifully."
    },
    {
      name: "Amanda Foster",
      title: "Audi R8 Owner",
      image: "https://images.pexels.com/photos/1181424/pexels-photo-1181424.jpeg",
      rating: 5,
      text: "Incredible attention to detail and customer care. They explained every step of the process and delivered results that exceeded my expectations. My Audi has never received so many compliments!"
    }
  ]

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % testimonials.length)
    }, 5000)

    return () => clearInterval(interval)
  }, [testimonials.length])

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % testimonials.length)
  }

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + testimonials.length) % testimonials.length)
  }

  const goToSlide = (index) => {
    setCurrentSlide(index)
  }

  return (
    <section id="testimonials" className={`${styles.testimonials} section-padding`}>
      <div className="container">
        <div className={`${styles.sectionHeader} ${isVisible ? 'animate-fadeInUp' : ''}`}>
          <h2>What Our Clients Say</h2>
          <p>Don't just take our word for it. Here's what luxury car owners say about our premium detailing services.</p>
        </div>

        <div className={styles.testimonialsContainer}>
          <div className={styles.slider}>
            <div 
              className={styles.slidesWrapper}
              style={{ transform: `translateX(-${currentSlide * 100}%)` }}
            >
              {testimonials.map((testimonial, index) => (
                <div key={index} className={styles.slide}>
                  <div className={styles.testimonialCard}>
                    <div className={styles.rating}>
                      {[...Array(testimonial.rating)].map((_, i) => (
                        <span key={i} className={styles.star}>★</span>
                      ))}
                    </div>
                    
                    <blockquote className={styles.quote}>
                      "{testimonial.text}"
                    </blockquote>
                    
                    <div className={styles.author}>
                      <div className={styles.authorImage}>
                        <img 
                          src={testimonial.image} 
                          alt={testimonial.name}
                          onError={(e) => {
                            e.target.style.display = 'none'
                          }}
                        />
                      </div>
                      <div className={styles.authorInfo}>
                        <h4>{testimonial.name}</h4>
                        <p>{testimonial.title}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className={styles.navigation}>
            <button 
              className={styles.navButton}
              onClick={prevSlide}
              aria-label="Previous testimonial"
            >
              ‹
            </button>
            <button 
              className={styles.navButton}
              onClick={nextSlide}
              aria-label="Next testimonial"
            >
              ›
            </button>
          </div>

          <div className={styles.dots}>
            {testimonials.map((_, index) => (
              <button
                key={index}
                className={`${styles.dot} ${index === currentSlide ? styles.active : ''}`}
                onClick={() => goToSlide(index)}
                aria-label={`Go to testimonial ${index + 1}`}
              />
            ))}
          </div>
        </div>

        <div className={`${styles.statsSection} ${isVisible ? 'animate-fadeInUp' : ''}`}>
          <div className={styles.stat}>
            <h3>500+</h3>
            <p>Happy Clients</p>
          </div>
          <div className={styles.stat}>
            <h3>5.0</h3>
            <p>Average Rating</p>
          </div>
          <div className={styles.stat}>
            <h3>100%</h3>
            <p>Satisfaction Rate</p>
          </div>
          <div className={styles.stat}>
            <h3>5+</h3>
            <p>Years Experience</p>
          </div>
        </div>
      </div>
    </section>
  )
}
