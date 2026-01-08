import nodemailer from 'nodemailer'
import path from 'path'

// In-memory storage for appointments with 24-hour expiration
let appointments = []

// Sanitize input to prevent XSS attacks
function sanitizeInput(str) {
  if (typeof str !== 'string') return str
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
}

// Validate email format
function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email) && email.length <= 254
}

// Validate phone format (basic)
function isValidPhone(phone) {
  const phoneRegex = /^[\d\s\-\(\)\+]+$/
  return phoneRegex.test(phone) && phone.length <= 20
}

// Clean up expired appointments (older than 24 hours)
function cleanupExpiredAppointments() {
  const now = new Date()
  appointments = appointments.filter(appt => {
    const apptDate = new Date(appt.date)
    const hoursDiff = (now - apptDate) / (1000 * 60 * 60)
    return hoursDiff < 24
  })
}

// Clean up every hour
setInterval(cleanupExpiredAppointments, 1000 * 60 * 60)

// IMPORTANT: Never hardcode credentials! Use environment variables.
// Create a .env.local file with SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST,
  port: process.env.SMTP_PORT ? parseInt(process.env.SMTP_PORT) : 587,
  secure: false,
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS,
  },
})

function convertTo24Hour(time12h) {
  const [time, modifier] = time12h.split(' ')
  let [hours, minutes] = time.split(':')
  if (hours === '12') {
    hours = '00'
  }
  if (modifier === 'PM') {
    hours = parseInt(hours, 10) + 12
  }
  return `${hours.toString().padStart(2, '0')}:${minutes}`
}

function isConflict(newAppointment) {
  // Clean up expired appointments before checking conflicts
  cleanupExpiredAppointments()
  
  const newTime24 = convertTo24Hour(newAppointment.time)
  const newStart = new Date(newAppointment.date + 'T' + newTime24)
  const newEnd = new Date(newStart.getTime() + newAppointment.duration * 60000)

  console.log('Checking conflict for:', {
    date: newAppointment.date,
    time: newAppointment.time,
    time24: newTime24,
    duration: newAppointment.duration,
    newStart: newStart.toISOString(),
    newEnd: newEnd.toISOString(),
    totalAppointments: appointments.length
  })

  for (const appt of appointments) {
    if (appt.canceled) continue
    
    const apptTime24 = convertTo24Hour(appt.time)
    const apptStart = new Date(appt.date + 'T' + apptTime24)
    const apptEnd = new Date(apptStart.getTime() + appt.duration * 60000)

    console.log('Comparing with existing appointment:', {
      date: appt.date,
      time: appt.time,
      time24: apptTime24,
      duration: appt.duration,
      apptStart: apptStart.toISOString(),
      apptEnd: apptEnd.toISOString()
    })

    if (
      (newStart >= apptStart && newStart < apptEnd) ||
      (newEnd > apptStart && newEnd <= apptEnd) ||
      (newStart <= apptStart && newEnd >= apptEnd)
    ) {
      console.log('CONFLICT DETECTED!')
      return true
    }
  }
  console.log('No conflict found')
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
    message,
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

  // Validate email format to prevent injection attacks
  if (!isValidEmail(email)) {
    return res.status(400).json({ error: 'Invalid email format' })
  }

  // Validate phone format
  if (!isValidPhone(phone)) {
    return res.status(400).json({ error: 'Invalid phone format' })
  }

  // Sanitize all user inputs to prevent XSS
  const newAppointment = {
    id: Date.now().toString(),
    name: sanitizeInput(name),
    email: sanitizeInput(email),
    phone: sanitizeInput(phone),
    vehicle: sanitizeInput(vehicle),
    service: sanitizeInput(service),
    date: sanitizeInput(date),
    time: sanitizeInput(time),
    addons: Array.isArray(addons) ? addons.map(sanitizeInput) : [],
    duration,
    message: sanitizeInput(message || ''),
    canceled: false,
  }

  // Conflict detection temporarily disabled
  // if (isConflict(newAppointment)) {
  //   return res.status(409).json({ error: 'Appointment time conflicts with an existing booking' })
  // }

  appointments.push(newAppointment)

  try {
    // SMTP is configured directly in the file, so always try to send emails
    const logoPath = path.join(process.cwd(), 'public', 'gardenbstate.png')
    
    console.log('Attempting to send emails...')
    
    // Send email to admin
    await transporter.sendMail({
      from: `"Garden State Detailing" <gardenstatedetailingllc@gmail.com>`,
      to: 'gardenstatedetailingllc@gmail.com',
      subject: 'New Detail Appointment Request',
      html: createAdminEmailTemplate(newAppointment),
      attachments: [{
        filename: 'logo.png',
        path: logoPath,
        cid: 'logo'
      }]
    })

    console.log('Admin email sent successfully')

    // Send confirmation email to customer
    await transporter.sendMail({
      from: `"Milton from Garden State Detailing" <toshidelay@gmail.com>`,
      to: email,
      subject: 'Thanks for Choosing Garden State Detailing!',
      html: createCustomerEmailTemplate(newAppointment),
      attachments: [{
        filename: 'logo.png',
        path: logoPath,
        cid: 'logo'
      }]
    })

    console.log('Customer email sent successfully')

    return res.status(200).json({ 
      message: 'Appointment booked successfully! Confirmation emails sent.', 
      appointmentId: newAppointment.id 
    })
  } catch (error) {
    console.error('Email sending error:', error)
    // Still return success since appointment was booked
    return res.status(200).json({ 
      message: 'Appointment booked successfully! (Email sending failed - please check SMTP configuration)', 
      appointmentId: newAppointment.id 
    })
  }
}

// Create professional HTML email templates
function createAdminEmailTemplate(appointment) {
  return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Appointment Request</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
        .logo { max-width: 120px; height: auto; margin-bottom: 15px; }
        .content { padding: 30px; }
        .appointment-details { background-color: #f8f9fa; border-left: 4px solid #3498db; padding: 20px; margin: 20px 0; border-radius: 4px; }
        .detail-row { margin: 10px 0; }
        .label { font-weight: bold; color: #2c3e50; }
        .value { color: #34495e; }
        .footer { background-color: #ecf0f1; padding: 20px; text-align: center; color: #7f8c8d; border-radius: 0 0 8px 8px; }
        .btn { display: inline-block; padding: 12px 24px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="cid:logo" alt="Garden State Detailing" class="logo">
            <h1>New Appointment Request</h1>
        </div>
        <div class="content">
            <p>Hey Milton,</p>
            <p>You have a new detail request that needs your attention:</p>
            
            <div class="appointment-details">
                <div class="detail-row">
                    <span class="label">Customer:</span> 
                    <span class="value">${appointment.name}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Phone:</span> 
                    <span class="value">${appointment.phone}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Email:</span> 
                    <span class="value">${appointment.email}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Vehicle:</span> 
                    <span class="value">${appointment.vehicle}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Package:</span> 
                    <span class="value">${appointment.service}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Add-ons:</span> 
                    <span class="value">${appointment.addons && appointment.addons.length > 0 ? appointment.addons.join(', ') : 'None'}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Date:</span> 
                    <span class="value">${appointment.date}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Time:</span> 
                    <span class="value">${appointment.time}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Duration:</span> 
                    <span class="value">${appointment.duration} minutes</span>
                </div>
                ${appointment.message ? `
                <div class="detail-row">
                    <span class="label">Additional Notes:</span> 
                    <span class="value">${appointment.message}</span>
                </div>
                ` : ''}
            </div>
            
            <p><strong>⏰ Remember to confirm this booking with the customer within 24 hours.</strong></p>
        </div>
        <div class="footer">
            <p>Garden State Detailing - Professional Auto Detailing Services</p>
            <p>Wharton, NJ | (973) 580-0014</p>
        </div>
    </div>
</body>
</html>
  `
}

function createCustomerEmailTemplate(appointment) {
  return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thank You for Choosing Garden State Detailing</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
        .logo { max-width: 120px; height: auto; margin-bottom: 15px; }
        .content { padding: 30px; }
        .appointment-summary { background-color: #f8f9fa; border-left: 4px solid #3498db; padding: 20px; margin: 20px 0; border-radius: 4px; }
        .detail-row { margin: 10px 0; }
        .label { font-weight: bold; color: #2c3e50; }
        .value { color: #34495e; }
        .highlight { background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; border: 1px solid #e9ecef; }
        .contact-info { background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }
        .footer { background-color: #2c3e50; color: white; padding: 20px; text-align: center; border-radius: 0 0 8px 8px; }
        .social-links { margin: 15px 0; }
        .social-links a { color: #3498db; text-decoration: none; margin: 0 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="cid:logo" alt="Garden State Detailing" class="logo">
            <h1>Thank You for Choosing Garden State Detailing!</h1>
        </div>
        <div class="content">
            <p>Hi ${appointment.name},</p>
            <p>Thank you for choosing Garden State Detailing! I've received your appointment request and I'm excited to work on your <strong>${appointment.vehicle}</strong>.</p>
            
            <div class="appointment-summary">
                <h3 style="margin-top: 0; color: #3498db;">📅 Your Appointment Request Details</h3>
                <div class="detail-row">
                    <span class="label">Package:</span> 
                    <span class="value">${appointment.service}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Add-ons:</span> 
                    <span class="value">${appointment.addons && appointment.addons.length > 0 ? appointment.addons.join(', ') : 'None'}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Date:</span> 
                    <span class="value">${appointment.date}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Time:</span> 
                    <span class="value">${appointment.time}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Estimated Duration:</span> 
                    <span class="value">${appointment.duration} minutes</span>
                </div>
                ${appointment.message ? `
                <div class="detail-row">
                    <span class="label">Additional Notes:</span> 
                    <span class="value">${appointment.message}</span>
                </div>
                ` : ''}
            </div>
            
            <div class="highlight" style="white-space: normal; overflow: visible;">
                <h3 style="margin-top: 0; color: #3498db;">🕐 What's Next?</h3>
                <p style="margin: 10px 0;">I'll personally reach out within <strong>24 hours</strong> to confirm these details and discuss any specific needs for your vehicle.</p>
            </div>
            
            <div class="contact-info">
                <h3 style="margin-top: 0; color: #3498db;">📞 Need to Reach Me?</h3>
                <p><strong>Phone/Text:</strong> (973) 580-0014</p>
                <p><strong>Email:</strong> gardenstatedetailingllc@gmail.com</p>
                <p><strong>Location:</strong> Wharton, NJ</p>
                <p><strong>Hours:</strong> Monday - Saturday, 9:00 AM - 3:30 PM</p>
            </div>
            
            <p>Looking forward to bringing your car back to life!</p>
            <p>Best regards,<br><strong>Milton</strong><br>Garden State Detailing</p>
        </div>
        <div class="footer">
            <p><strong>Garden State Detailing</strong></p>
            <p>Professional Auto Detailing Services</p>
            <p>Wharton, NJ | (973) 580-0014</p>
            <div class="social-links">
                <p>Follow us for tips and updates!</p>
            </div>
        </div>
    </div>
</body>
</html>
  `
}
