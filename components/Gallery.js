import { useState, useEffect } from 'react'
import Image from 'next/image'
import styles from '../styles/components/Gallery.module.css'

export default function Gallery() {
  const [isVisible, setIsVisible] = useState(false)
  const [selectedImage, setSelectedImage] = useState(null)
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true)
        }
      },
      { threshold: 0.1 }
    )

    const element = document.getElementById('gallery')
    if (element) {
      observer.observe(element)
    }

    return () => {
      if (element) {
        observer.unobserve(element)
      }
    }
  }, [])

  const galleryImages = [
    {
      id: 1,
      src: "https://images.pexels.com/photos/358070/pexels-photo-358070.jpeg",
      alt: "Luxury sports car exterior detailing",
      category: "exterior",
      title: "Ferrari 488 - Paint Correction"
    },
    {
      id: 2,
      src: "https://images.pexels.com/photos/210019/pexels-photo-210019.jpeg",
      alt: "Premium car interior detailing",
      category: "interior",
      title: "Lamborghini Interior - Leather Care"
    },
    {
      id: 3,
      src: "https://images.pexels.com/photos/1545743/pexels-photo-1545743.jpeg",
      alt: "Ceramic coating application",
      category: "coating",
      title: "Porsche 911 - Ceramic Coating"
    },
    {
      id: 4,
      src: "https://images.pexels.com/photos/1149137/pexels-photo-1149137.jpeg",
      alt: "Luxury sedan detailing",
      category: "exterior",
      title: "Mercedes S-Class - Full Detail"
    },
    {
      id: 5,
      src: "https://images.pexels.com/photos/1592384/pexels-photo-1592384.jpeg",
      alt: "Sports car paint protection",
      category: "coating",
      title: "BMW M5 - Paint Protection Film"
    },
    {
      id: 6,
      src: "https://images.pexels.com/photos/1719648/pexels-photo-1719648.jpeg",
      alt: "Premium interior cleaning",
      category: "interior",
      title: "Audi R8 - Interior Restoration"
    },
    {
      id: 7,
      src: "https://images.pexels.com/photos/1007410/pexels-photo-1007410.jpeg",
      alt: "Exotic car detailing",
      category: "exterior",
      title: "McLaren 720S - Show Prep"
    },
    {
      id: 8,
      src: "https://images.pexels.com/photos/1335077/pexels-photo-1335077.jpeg",
      alt: "Luxury SUV detailing",
      category: "exterior",
      title: "Range Rover - Premium Detail"
    },
    {
      id: 9,
      src: "https://images.pexels.com/photos/1545902/pexels-photo-1545902.jpeg",
      alt: "Engine bay detailing",
      category: "engine",
      title: "Ferrari Engine Bay - Deep Clean"
    }
  ]

  const categories = [
    { key: 'all', label: 'All Work' },
    { key: 'exterior', label: 'Exterior' },
    { key: 'interior', label: 'Interior' },
    { key: 'coating', label: 'Protection' },
    { key: 'engine', label: 'Engine Bay' }
  ]

  const filteredImages = filter === 'all' 
    ? galleryImages 
    : galleryImages.filter(img => img.category === filter)

  const openLightbox = (image) => {
    setSelectedImage(image)
    document.body.style.overflow = 'hidden'
  }

  const closeLightbox = () => {
    setSelectedImage(null)
    document.body.style.overflow = 'unset'
  }

  const nextImage = () => {
    const currentIndex = filteredImages.findIndex(img => img.id === selectedImage.id)
    const nextIndex = (currentIndex + 1) % filteredImages.length
    setSelectedImage(filteredImages[nextIndex])
  }

  const prevImage = () => {
    const currentIndex = filteredImages.findIndex(img => img.id === selectedImage.id)
    const prevIndex = (currentIndex - 1 + filteredImages.length) % filteredImages.length
    setSelectedImage(filteredImages[prevIndex])
  }

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (selectedImage) {
        if (e.key === 'Escape') closeLightbox()
        if (e.key === 'ArrowRight') nextImage()
        if (e.key === 'ArrowLeft') prevImage()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [selectedImage])

  return (
    <section id="gallery" className={`${styles.gallery} section-padding`}>
      <div className="container">
        <div className={`${styles.sectionHeader} ${isVisible ? 'animate-fadeInUp' : ''}`}>
          <h2>Our Work Gallery</h2>
          <p>Explore our portfolio of premium automotive detailing projects. Each vehicle receives our signature attention to detail and luxury care.</p>
        </div>

        <div className={`${styles.filterButtons} ${isVisible ? 'animate-fadeInUp' : ''}`}>
          {categories.map((category) => (
            <button
              key={category.key}
              className={`${styles.filterBtn} ${filter === category.key ? styles.active : ''}`}
              onClick={() => setFilter(category.key)}
            >
              {category.label}
            </button>
          ))}
        </div>

        <div className={styles.galleryGrid}>
          {filteredImages.map((image, index) => (
            <div 
              key={image.id}
              className={`${styles.galleryItem} ${isVisible ? 'animate-fadeInUp' : ''}`}
              style={{ animationDelay: `${index * 0.1}s` }}
              onClick={() => openLightbox(image)}
            >
              <div className={styles.imageWrapper}>
                <Image
                  src={image.src}
                  alt={image.alt}
                  fill
                  style={{ objectFit: 'cover' }}
                  quality={80}
                />
                <div className={styles.overlay}>
                  <div className={styles.overlayContent}>
                    <h4>{image.title}</h4>
                    <span className={styles.viewIcon}>👁️</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className={`${styles.ctaSection} ${isVisible ? 'animate-fadeInUp' : ''}`}>
          <h3>Ready to See Your Car Transformed?</h3>
          <p>Join our gallery of satisfied customers and experience the luxury detailing difference.</p>
          <button 
            onClick={() => document.getElementById('booking').scrollIntoView({ behavior: 'smooth' })}
            className="btn-primary"
          >
            Book Your Detail
          </button>
        </div>
      </div>

      {/* Lightbox */}
      {selectedImage && (
        <div className={styles.lightbox} onClick={closeLightbox}>
          <div className={styles.lightboxContent} onClick={(e) => e.stopPropagation()}>
            <button className={styles.closeBtn} onClick={closeLightbox}>×</button>
            <button className={styles.prevBtn} onClick={prevImage}>‹</button>
            <button className={styles.nextBtn} onClick={nextImage}>›</button>
            
            <div className={styles.lightboxImage}>
              <Image
                src={selectedImage.src}
                alt={selectedImage.alt}
                fill
                style={{ objectFit: 'contain' }}
                quality={90}
              />
            </div>
            
            <div className={styles.lightboxInfo}>
              <h4>{selectedImage.title}</h4>
              <p>{selectedImage.alt}</p>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
