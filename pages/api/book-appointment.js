import nodemailer from 'nodemailer'

let appointments = []

const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST || 'smtp.gmail.com',
  port: process.env.SMTP_PORT ? parseInt(process.env.SMTP_PORT) : 587,
  secure: false,
  auth: {
    user: process.env.SMTP_USER || 'toshidelay@gmail.com',
    pass: process.env.SMTP_PASS || 'jaqe olxj bzph qcss',
  },
})

function isConflict(newAppointment) {
  const newStart = new Date(newAppointment.date + 'T' + newAppointment.time)
  const newEnd = new Date(newStart.getTime() + newAppointment.duration * 60000)

  for (const appt of appointments) {
    if (appt.canceled) continue
    const apptStart = new Date(appt.date + 'T' + appt.time)
    const apptEnd = new Date(apptStart.getTime() + appt.duration * 60000)

    if (
      (newStart >= apptStart && newStart < apptEnd) ||
      (newEnd > apptStart && newEnd <= apptEnd) ||
      (newStart <= apptStart && newEnd >= apptEnd)
    ) {
      return true
    }
  }
  return false
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  const {
    name,
    email,
    phone,
    vehicle,
    service,
    date,
    time,
    addons,
    duration,
  } = req.body

  if (
    !name ||
    !email ||
    !phone ||
    !vehicle ||
    !service ||
    !date ||
    !time ||
    !duration
  ) {
    return res.status(400).json({ error: 'Missing required fields' })
  }

  const newAppointment = {
    id: Date.now().toString(),
    name,
    email,
    phone,
    vehicle,
    service,
    date,
    time,
    addons: addons || [],
    duration,
    canceled: false,
  }

  if (isConflict(newAppointment)) {
    return res.status(409).json({ error: 'Appointment time conflicts with an existing booking' })
  }

  appointments.push(newAppointment)

  try {
    // Send email to admin
    await transporter.sendMail({
      from: "Garden State Detailing" <${process.env.SMTP_USER}>,
      to: 'toshidelay@gmail.com',
      subject: 'New Detail Appointment Request',
      text: 
Hey Milton,

You have a new detail request:

Customer: ${name}
Contact: ${phone} | ${email}
Vehicle: ${vehicle}
Package: ${service}
Add-ons: ${addons ? addons.join(', ') : 'None'}
Date: ${date}
Time: ${time}
Duration: ${duration} minutes

Remember to confirm this booking with the customer within 24 hours.
      ,
    })

    // Send confirmation email to customer
    await transporter.sendMail({
      from: "Milton from Garden State Detailing" <${process.env.SMTP_USER}>,
      to: email,
      subject: 'Thanks for Choosing Garden State Detailing!',
      text: 
Hi ${name},

Thanks for choosing Garden State Detailing! I've received your appointment request and I'm excited to work on your ${vehicle}.

Here are the details of your requested appointment:

Package: ${service}
Add-ons: ${addons ? addons.join(', ') : 'None'}
Date: ${date}
Time: ${time}
Estimated Duration: ${duration} minutes

I'll personally reach out within 24 hours to confirm these details and discuss any specific needs for your vehicle. If you need to reach me before then, you can call or text me at (973) 580-0014 or email me at gardenstatedetailingllc@gmail.com.

Looking forward to bringing your car back to life!

Best regards,
Milton
Garden State Detailing
      ,
    })

    return res.status(200).json({ message: 'Appointment booked successfully', appointmentId: newAppointment.id })
  } catch (error) {
    console.error('Email sending error:', error)
    return res.status(500).json({ error: Failed to send confirmation emails: ${error.message} })
  }
}
