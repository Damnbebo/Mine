import { useState, useEffect } from 'react'
import styles from '../styles/components/Services.module.css'

export default function Services() {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true)
        }
      },
      { threshold: 0.1 }
    )

    const element = document.getElementById('services')
    if (element) {
      observer.observe(element)
    }

    return () => {
      if (element) {
        observer.unobserve(element)
      }
    }
  }, [])

  const services = [
    {
      title: "Premium Exterior Detailing",
      description: "Complete exterior wash, clay bar treatment, paint correction, and premium wax application for a showroom finish.",
      features: ["Paint Correction", "Clay Bar Treatment", "Premium Wax", "Tire & Rim Cleaning"],
      icon: "🚗"
    },
    {
      title: "Luxury Interior Detailing",
      description: "Deep cleaning and conditioning of all interior surfaces including leather, fabric, and premium materials.",
      features: ["Leather Conditioning", "Steam Cleaning", "Fabric Protection", "Dashboard Care"],
      icon: "🪑"
    },
    {
      title: "Ceramic Coating Protection",
      description: "Advanced ceramic coating application providing long-lasting protection and enhanced gloss for your vehicle.",
      features: ["9H Hardness", "UV Protection", "Hydrophobic Effect", "5-Year Warranty"],
      icon: "🛡️"
    },
    {
      title: "Paint Protection Film",
      description: "Invisible protection film application to safeguard your vehicle's paint from chips, scratches, and environmental damage.",
      features: ["Self-Healing Technology", "Crystal Clear", "10-Year Warranty", "Custom Fit"],
      icon: "✨"
    },
    {
      title: "Engine Bay Detailing",
      description: "Professional engine bay cleaning and detailing to maintain your vehicle's mechanical aesthetics and performance.",
      features: ["Degreasing", "Steam Cleaning", "Component Protection", "Aesthetic Enhancement"],
      icon: "⚙️"
    },
    {
      title: "Headlight Restoration",
      description: "Professional headlight restoration service to improve visibility and enhance your vehicle's appearance.",
      features: ["UV Damage Repair", "Clarity Restoration", "Protective Coating", "Safety Enhancement"],
      icon: "💡"
    }
  ]

  return (
    <section id="services" className={`${styles.services} section-padding`}>
      <div className="container">
        <div className={`${styles.sectionHeader} ${isVisible ? 'animate-fadeInUp' : ''}`}>
          <h2>Our Premium Services</h2>
          <p>Experience the finest automotive care with our comprehensive detailing services designed for luxury vehicles.</p>
        </div>

        <div className={styles.servicesGrid}>
          {services.map((service, index) => (
            <div 
              key={index}
              className={`${styles.serviceCard} ${isVisible ? 'animate-fadeInUp' : ''}`}
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className={styles.serviceIcon}>
                <span>{service.icon}</span>
              </div>
              <div className={styles.serviceContent}>
                <h3>{service.title}</h3>
                <p>{service.description}</p>
                <ul className={styles.featureList}>
                  {service.features.map((feature, featureIndex) => (
                    <li key={featureIndex}>
                      <span className={styles.checkmark}>✓</span>
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
              <div className={styles.serviceFooter}>
                <button className="btn-secondary">Learn More</button>
              </div>
            </div>
          ))}
        </div>

        <div className={`${styles.ctaSection} ${isVisible ? 'animate-fadeInUp' : ''}`}>
          <h3>Ready to Transform Your Vehicle?</h3>
          <p>Contact us today to schedule your premium detailing service and experience the difference.</p>
          <button 
            onClick={() => document.getElementById('booking').scrollIntoView({ behavior: 'smooth' })}
            className="btn-primary"
          >
            Book Your Service
          </button>
        </div>
      </div>
    </section>
  )
}
