class SimulationWidget {
  constructor(container, id) {
    this.container = container;
    this.id = id;
    this.init();
  }

  init() {
    const ws = new WebSocket(`ws://${window.location.host}/ws/${this.id}`);
    const canvas = document.createElement('canvas');
    this.ctx = canvas.getContext('2d');
    this.container.appendChild(canvas);

    ws.onmessage = (evt) => {
      const frame = JSON.parse(evt.data);
      this.draw(frame);
    };
  }

  draw({x, y}) {
    const {ctx} = this;
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    ctx.beginPath();
    ctx.arc(50 + x*10, 50 - y*50, 5, 0, 2*Math.PI);
    ctx.fill();
  }
}

// Scan markdown code blocks marked as simulation
window.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('pre code.language-simulation').forEach((block, i) => {
    const id = `sim-${i}`;
    const container = document.createElement('div');
    block.parentNode.replaceWith(container);
    new SimulationWidget(container, id);
    // POST to /simulate to start
    fetch('/simulate', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({id}) });
  });
});