import fs from 'fs'
import path from 'path'
import nodemailer from 'nodemailer'

const filePath = path.join(process.cwd(), 'appointments.json')

// Ensure file exists
if (!fs.existsSync(filePath)) {
  fs.writeFileSync(filePath, '[]')
}

let appointments = JSON.parse(fs.readFileSync(filePath, 'utf8'))

const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST || 'smtp.gmail.com',
  port: parseInt(process.env.SMTP_PORT || '587'),
  secure: false,
  auth: {
    user: process.env.SMTP_USER || 'toshidelay@gmail.com',
    pass: process.env.SMTP_PASS || 'jaqe olxj bzph qcss',
  },
})

function isConflict(newAppt) {
  const newStart = new Date(`${newAppt.date}T${newAppt.time}`)
  const newEnd = new Date(newStart.getTime() + newAppt.duration * 60000)

  return appointments.some(appt => {
    if (appt.canceled) return false
    const apptStart = new Date(`${appt.date}T${appt.time}`)
    const apptEnd = new Date(apptStart.getTime() + appt.duration * 60000)
    return (
      (newStart >= apptStart && newStart < apptEnd) ||
      (newEnd > apptStart && newEnd <= apptEnd) ||
      (newStart <= apptStart && newEnd >= apptEnd)
    )
  })
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' })

  const { name, email, phone, vehicle, service, date, time, addons, duration } = req.body
  if (!name || !email || !phone || !vehicle || !service || !date || !time || !duration)
    return res.status(400).json({ error: 'Missing required fields' })

  const newAppointment = {
    id: Date.now().toString(),
    name, email, phone, vehicle, service, date, time,
    addons: addons || [], duration, canceled: false
  }

  if (isConflict(newAppointment)) {
    return res.status(409).json({ error: 'Appointment time conflicts with an existing booking' })
  }

  appointments.push(newAppointment)
  fs.writeFileSync(filePath, JSON.stringify(appointments, null, 2))

  const logoCid = 'logo@gardenstatedetailing'

  const htmlContent = (recipientName, isCustomer = false) => `
    <div style="font-family:Arial,sans-serif;padding:20px">
      <div style="text-align:center;">
        <img src="cid:${logoCid}" alt="Logo" style="max-width:150px;margin-bottom:20px"/>
      </div>
      <h2 style="color:#c62828;">${isCustomer ? 'Thank You for Booking!' : 'New Appointment Request'}</h2>
      <p>Hi ${recipientName},</p>
      <p>${isCustomer 
        ? `Thanks for choosing <strong>Garden State Detailing</strong>! I've received your request and will follow up within 24 hours.` 
        : `You’ve received a new appointment request.`}</p>
      <ul>
        <li><strong>Customer:</strong> ${name}</li>
        <li><strong>Contact:</strong> ${phone} | ${email}</li>
        <li><strong>Vehicle:</strong> ${vehicle}</li>
        <li><strong>Package:</strong> ${service}</li>
        <li><strong>Add-ons:</strong> ${addons.length ? addons.join(', ') : 'None'}</li>
        <li><strong>Date:</strong> ${date}</li>
        <li><strong>Time:</strong> ${time}</li>
        <li><strong>Duration:</strong> ${duration} mins</li>
      </ul>
      <p>${isCustomer 
        ? `If you have questions, call/text me at <a href="tel:9735800014">(973) 580-0014</a> or email <a href="mailto:gardenstatedetailingllc@gmail.com">gardenstatedetailingllc@gmail.com</a>.` 
        : 'Please confirm this appointment within 24 hours.'}</p>
      <p style="margin-top:30px;">- Milton<br><strong>Garden State Detailing</strong></p>
    </div>
  `

  try {
    await transporter.sendMail({
      from: `"Garden State Detailing" <${process.env.SMTP_USER}>`,
      to: 'toshidelay@gmail.com',
      subject: 'New Detail Appointment Request',
      html: htmlContent('Milton'),
      attachments: [{
        filename: 'logo.png',
        path: './public/gardenbstate.png', // Or wherever your public logo is
        cid: logoCid
      }]
    })

    await transporter.sendMail({
      from: `"Milton @ Garden State Detailing" <${process.env.SMTP_USER}>`,
      to: email,
      subject: 'Your Appointment Request Received!',
      html: htmlContent(name, true),
      attachments: [{
        filename: 'logo.png',
        path: './public/GardenStae.png',
        cid: logoCid
      }]
    })

    return res.status(200).json({ message: 'Appointment booked successfully', appointmentId: newAppointment.id })
  } catch (err) {
    console.error('Email error:', err)
    return res.status(500).json({ error: 'Failed to send confirmation emails' })
  }
}
