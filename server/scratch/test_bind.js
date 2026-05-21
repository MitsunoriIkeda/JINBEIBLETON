const dgram = require('dgram');
const s = dgram.createSocket('udp4');
s.on('error', (err) => {
  console.log(`❌ BIND ERROR: ${err.message}`);
  process.exit(1);
});
s.bind(0, () => {
  console.log(`✅ SUCCESS! Bound to random port: ${s.address().port}`);
  process.exit(0);
});
