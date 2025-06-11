import '../styles/globals.css'
import Head from 'next/head'

export default function App({ Component, pageProps }) {
  return (
    <>
      <Head>
        <title>Garden State Detailing</title>
        <meta name="description" content="Professional automotive detailing services by Garden State Detailing. Meticulous care for your vehicle with premium products and exceptional customer service." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
        <meta property="og:title" content="Garden State Detailing" />
        <meta property="og:description" content="Professional automotive detailing services by Garden State Detailing." />
        <meta property="og:type" content="website" />
      </Head>
      <Component {...pageProps} />
    </>
  )
}
