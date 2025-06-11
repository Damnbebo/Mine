import Layout from '../components/Layout'
import Hero from '../components/Hero'
import Services from '../components/Services'
import Pricing from '../components/Pricing'
import Testimonials from '../components/Testimonials'
import Gallery from '../components/Gallery'
import BookingForm from '../components/BookingForm'

export default function Home() {
  return (
    <Layout>
      <Hero />
      <Services />
      <Pricing />
      <Testimonials />
      <Gallery />
      <BookingForm />
    </Layout>
  )
}
