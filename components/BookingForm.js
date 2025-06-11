import { useState } from 'react'
import styles from '../styles/components/BookingForm.module.css'

const PACKAGES = [
  { label: 'Basic Detail - Sedan (1h 30m) - $100.00', value: 'Basic Detail - Sedan', duration: 90, price: 100 },
  { label: 'Basic Detail - SUV/Truck (1h 30m) - $120.00', value: 'Basic Detail - SUV/Truck', duration: 90, price: 120 },
  { label: 'Standard Detail - Sedan (2h 30m) - $150.00', value: 'Standard Detail - Sedan', duration: 150, price: 150 },
  { label: 'Standard Detail - SUV/Truck (2h 30m) - $180.00', value: 'Standard Detail - SUV/Truck', duration: 150, price: 180 },
  { label: 'Premium Detail - Sedan (3h 30m) - $220.00', value: 'Premium Detail - Sedan', duration: 210, price: 220 },
  { label: 'Premium Detail - SUV/Truck (3h 30m) - $260.00', value: 'Premium Detail - SUV/Truck', duration: 210, price: 260 }
]

const ADDONS = [
  { label: 'Engine Bay Cleaning (+$35.00)', value: 'Engine Bay Cleaning', price: 35 },
  { label: 'Pet Hair Removal (+$35.00)', value: 'Pet Hair Removal', price: 35 }
]

const TIME_SLOTS = [
  '9:00 AM', '9:30 AM', '10:00 AM', '10:30 AM', '11:00 AM', '11:30 AM',
  '12:00 PM', '12:30 PM', '1:00 PM', '1:30 PM', '2:00 PM', '2:30 PM',
  '3:00 PM', '3:30 PM'
]

export default function BookingForm() {

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    vehicle: '',
    service: '',
    addons: [],
    date: '',
    time: '',
    message: ''
  })
  const [errors, setErrors] = useState({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [submitMessage, setSubmitMessage] = useState('')

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target

    if (type === 'checkbox') {
      let newAddons = [...formData.addons]
      if (checked) {
        newAddons.push(value)
      } else {
        newAddons = newAddons.filter(a => a !== value)
      }
      setFormData(prev => ({ ...prev, addons: newAddons }))
    } else {
      setFormData(prev => ({ ...prev, [name]: value }))
    }

    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }))
    }
  }

  const validateForm = () => {
    const newErrors = {}

    if (!formData.name.trim()) newErrors.name = 'Name is required'
    if (!formData.email.trim()) newErrors.email = 'Email is required'
    else if (!/\S+@\S+\.\S+/.test(formData.email)) newErrors.email = 'Email is invalid'
    if (!formData.phone.trim()) newErrors.phone = 'Phone number is required'
    else if (!/^\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$/.test(formData.phone)) newErrors.phone = 'Phone number is invalid'
    if (!formData.vehicle.trim()) newErrors.vehicle = 'Vehicle information is required'
    if (!formData.service) newErrors.service = 'Please select a service'
    if (!formData.date) newErrors.date = 'Please select a date'
    else {
      const selectedDate = new Date(formData.date)
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      if (selectedDate < today) newErrors.date = 'Please select a future date'
    }
    if (!formData.time) newErrors.time = 'Please select a time'

    return newErrors
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitMessage('')
    const newErrors = validateForm()
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }

    setIsSubmitting(true)

    const selectedPackage = PACKAGES.find(p => p.value === formData.service)
    const duration = selectedPackage ? selectedPackage.duration : 90

    try {
      const response = await fetch('/api/book-appointment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          duration,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        setSubmitMessage(data.error || 'Failed to book appointment')
        setIsSubmitting(false)
        return
      }

      setIsSubmitted(true)
      setSubmitMessage('Booking successful! Confirmation email sent.')

      setTimeout(() => {
        setFormData({
          name: '',
          email: '',
          phone: '',
          vehicle: '',
          service: '',
          addons: [],
          date: '',
          time: '',
          message: ''
        })
        setIsSubmitted(false)
        setSubmitMessage('')
      }, 5000)
    } catch (error) {
      setSubmitMessage('An error occurred. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const getMinDate = () => {
    const today = new Date()
    return today.toISOString().split('T')[0]
  }

  return (
    <section id="booking" className={`${styles.booking} section-padding`}>
      <div className="container">
        <div className={styles.sectionHeader}>
          <h2>Schedule Your Detail</h2>
          <p>Ready to bring your car back to life? Book your professional detailing service with Garden State Detailing today.</p>
        </div>

        <div className={styles.bookingContainer}>
          <div className={styles.bookingInfo}>
            <h3>Why Choose Us?</h3>
            <div className={styles.features}>
              <div className={styles.feature}>
                <span className={styles.featureIcon}>🏆</span>
                <div>
                  <h4>Quality Service</h4>
                  <p>Top-grade products and meticulous attention to detail for your vehicle</p>
                </div>
              </div>
              <div className={styles.feature}>
                <span className={styles.featureIcon}>⏰</span>
                <div>
                  <h4>Convenient Hours</h4>
                  <p>Flexible scheduling Monday through Saturday, 9 AM to 3:30 PM</p>
                </div>
              </div>
              <div className={styles.feature}>
                <span className={styles.featureIcon}>🛡️</span>
                <div>
                  <h4>Personal Care</h4>
                  <p>Dedicated one-on-one service from a passionate car enthusiast</p>
                </div>
              </div>
              <div className={styles.feature}>
                <span className={styles.featureIcon}>🚗</span>
                <div>
                  <h4>All Vehicles Welcome</h4>
                  <p>From daily drivers to luxury cars, every vehicle gets VIP treatment</p>
                </div>
              </div>
            </div>

            <div className={styles.contactInfo}>
              <h4>Contact Information</h4>
              <p>📞 (973) 580-0014</p>
              <p>📧 gardenstatedetailingllc@gmail.com</p>
              <p>📍 Wharton, NJ</p>
              <p>🕒 Mon-Sat: 9AM-3:30PM</p>
            </div>
          </div>

          <form className={styles.bookingForm} onSubmit={handleSubmit}>
            <div className={styles.formGroup}>
              <label htmlFor="name">Full Name *</label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className={errors.name ? styles.error : ''}
                placeholder="Enter your full name"
              />
              {errors.name && <span className={styles.errorText}>{errors.name}</span>}
            </div>

            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label htmlFor="email">Email Address *</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className={errors.email ? styles.error : ''}
                  placeholder="your@email.com"
                />
                {errors.email && <span className={styles.errorText}>{errors.email}</span>}
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="phone">Phone Number *</label>
                <input
                  type="tel"
                  id="phone"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  className={errors.phone ? styles.error : ''}
                  placeholder="(973) 580-0014"
                />
                {errors.phone && <span className={styles.errorText}>{errors.phone}</span>}
              </div>
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="vehicle">Vehicle Information *</label>
              <input
                type="text"
                id="vehicle"
                name="vehicle"
                value={formData.vehicle}
                onChange={handleChange}
                className={errors.vehicle ? styles.error : ''}
                placeholder="e.g., 2020 Honda Civic, 2018 Ford F-150"
              />
              {errors.vehicle && <span className={styles.errorText}>{errors.vehicle}</span>}
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="service">Select Package *</label>
              <select
                id="service"
                name="service"
                value={formData.service}
                onChange={handleChange}
                className={errors.service ? styles.error : ''}
              >
                <option value="">Choose a package...</option>
                {PACKAGES.map((pkg, index) => (
                  <option key={index} value={pkg.value}>{pkg.label}</option>
                ))}
              </select>
              {errors.service && <span className={styles.errorText}>{errors.service}</span>}
            </div>

            <div className={styles.formGroup}>
              <label>Add-ons (optional)</label>
              <div className={styles.addonsContainer}>
                {ADDONS.map((addon, index) => (
                  <label 
                    key={index} 
                    className={`${styles.addonCard} ${formData.addons.includes(addon.value) ? styles.selected : ''}`}
                  >
                    <input
                      type="checkbox"
                      name="addons"
                      value={addon.value}
                      checked={formData.addons.includes(addon.value)}
                      onChange={handleChange}
                    />
                    <span className={styles.addonCheckmark}></span>
                    <div className={styles.addonInfo}>
                      <div className={styles.addonName}>{addon.value}</div>
                      <div className={styles.addonPrice}>+${addon.price.toFixed(2)}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label htmlFor="date">Preferred Date *</label>
                <input
                  type="date"
                  id="date"
                  name="date"
                  value={formData.date}
                  onChange={handleChange}
                  min={getMinDate()}
                  className={errors.date ? styles.error : ''}
                />
                {errors.date && <span className={styles.errorText}>{errors.date}</span>}
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="time">Preferred Time *</label>
                <select
                  id="time"
                  name="time"
                  value={formData.time}
                  onChange={handleChange}
                  className={errors.time ? styles.error : ''}
                >
                  <option value="">Select time...</option>
                  {TIME_SLOTS.map((time, index) => (
                    <option key={index} value={time}>{time}</option>
                  ))}
                </select>
                {errors.time && <span className={styles.errorText}>{errors.time}</span>}
              </div>
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="message">Additional Notes</label>
              <textarea
                id="message"
                name="message"
                value={formData.message}
                onChange={handleChange}
                rows="4"
                placeholder="Any special requests or additional information..."
              />
            </div>

            {submitMessage && (
              <div className={styles.submitMessage}>{submitMessage}</div>
            )}

            <button 
              type="submit" 
              className={`btn-primary ${styles.submitBtn}`}
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <span className={styles.spinner}></span>
                  Submitting...
                </>
              ) : (
                'Book Appointment'
              )}
            </button>

            <p className={styles.disclaimer}>
              * Required fields. I'll personally reach out within 24 hours to confirm your appointment and discuss any specific needs for your vehicle.
            </p>
          </form>
        </div>
      </div>
    </section>
  )
}
