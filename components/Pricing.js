import { useState, useEffect } from 'react'
import styles from '../styles/components/Pricing.module.css'

export default function Pricing() {
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

    const element = document.getElementById('pricing')
    if (element) {
      observer.observe(element)
    }

    return () => {
      if (element) {
        observer.unobserve(element)
      }
    }
  }, [])

  const pricingPlans = [
    {
      name: "Basic Detail - Sedan",
      price: "$100",
      duration: "1h 30m",
      description: "Perfect for regular maintenance and keeping your sedan looking fresh.",
      features: [
        "Exterior hand wash",
        "Interior vacuum",
        "Window cleaning",
        "Tire shine",
        "Basic wipe down"
      ],
      popular: false
    },
    {
      name: "Basic Detail - SUV/Truck",
      price: "$120",
      duration: "1h 30m",
      description: "Basic detailing package tailored for larger vehicles.",
      features: [
        "Exterior hand wash",
        "Interior vacuum",
        "Window cleaning",
        "Tire shine",
        "Basic wipe down"
      ],
      popular: false
    },
    {
      name: "Standard Detail - Sedan",
      price: "$150",
      duration: "2h 30m",
      description: "Our most popular package for sedans offering comprehensive care.",
      features: [
        "Everything in Basic",
        "Thorough interior cleaning",
        "Leather/vinyl treatment",
        "Paint decontamination",
        "Wheels deep cleaning"
      ],
      popular: true
    },
    {
      name: "Standard Detail - SUV/Truck",
      price: "$180",
      duration: "2h 30m",
      description: "Comprehensive detailing package for larger vehicles.",
      features: [
        "Everything in Basic",
        "Thorough interior cleaning",
        "Leather/vinyl treatment",
        "Paint decontamination",
        "Wheels deep cleaning"
      ],
      popular: false
    },
    {
      name: "Premium Detail - Sedan",
      price: "$220",
      duration: "3h 30m",
      description: "The ultimate detailing experience for your sedan.",
      features: [
        "Everything in Standard",
        "Paint correction",
        "Ceramic spray coating",
        "Premium interior detail",
        "Engine bay cleaning"
      ],
      popular: false
    },
    {
      name: "Premium Detail - SUV/Truck",
      price: "$260",
      duration: "3h 30m",
      description: "The ultimate detailing experience for larger vehicles.",
      features: [
        "Everything in Standard",
        "Paint correction",
        "Ceramic spray coating",
        "Premium interior detail",
        "Engine bay cleaning"
      ],
      popular: false
    }
  ]

  const addOns = [
    { name: "Engine Bay Cleaning", price: "$35" },
    { name: "Pet Hair Removal", price: "$35" }
  ]

  return (
    <section id="pricing" className={`${styles.pricing} section-padding`}>
      <div className="container">
        <div className={`${styles.sectionHeader} ${isVisible ? 'animate-fadeInUp' : ''}`}>
          <h2>Transparent Pricing</h2>
          <p>Choose the perfect detailing package for your vehicle. All prices include premium products and professional service.</p>
        </div>

        <div className={styles.pricingGrid}>
          {pricingPlans.map((plan, index) => (
            <div 
              key={index}
              className={`${styles.pricingCard} ${plan.popular ? styles.popular : ''} ${isVisible ? 'animate-fadeInUp' : ''}`}
              style={{ animationDelay: `${index * 0.2}s` }}
              data-type={plan.name.toLowerCase().includes('suv') ? 'suv' : 'sedan'}
            >
              {plan.popular && (
                <div className={styles.popularBadge}>
                  Most Popular
                </div>
              )}
              
              <div className={styles.cardHeader}>
                <h3>{plan.name}</h3>
                <div className={styles.priceSection}>
                  <span className={styles.price}>{plan.price}</span>
                  <span className={styles.duration}>{plan.duration}</span>
                </div>
                <p className={styles.description}>{plan.description}</p>
              </div>

              <div className={styles.cardBody}>
                <ul className={styles.featureList}>
                  {plan.features.map((feature, featureIndex) => (
                    <li key={featureIndex}>
                      <span className={styles.checkmark}>✓</span>
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>

              <div className={styles.cardFooter}>
                <button 
                  className={plan.popular ? "btn-primary" : "btn-secondary"}
                  onClick={() => document.getElementById('booking').scrollIntoView({ behavior: 'smooth' })}
                >
                  Choose This Package
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className={`${styles.addOnsSection} ${isVisible ? 'animate-fadeInUp' : ''}`}>
          <h3>Additional Services</h3>
          <p>Enhance your detailing package with these premium add-on services.</p>
          
          <div className={styles.addOnsGrid}>
            {addOns.map((addon, index) => (
              <div key={index} className={styles.addOnCard}>
                <span className={styles.addOnName}>{addon.name}</span>
                <span className={styles.addOnPrice}>{addon.price}</span>
              </div>
            ))}
          </div>
        </div>

        <div className={`${styles.guaranteeSection} ${isVisible ? 'animate-fadeInUp' : ''}`}>
          <div className={styles.guaranteeContent}>
            <h3>100% Satisfaction Guarantee</h3>
            <p>We stand behind our work with a complete satisfaction guarantee. If you're not completely happy with our service, we'll make it right or provide a full refund.</p>
            <div className={styles.guaranteeFeatures}>
              <div className={styles.guaranteeItem}>
                <span className={styles.guaranteeIcon}>🛡️</span>
                <span>Quality Assurance</span>
              </div>
              <div className={styles.guaranteeItem}>
                <span className={styles.guaranteeIcon}>💯</span>
                <span>100% Satisfaction</span>
              </div>
              <div className={styles.guaranteeItem}>
                <span className={styles.guaranteeIcon}>🔄</span>
                <span>Money Back Guarantee</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
