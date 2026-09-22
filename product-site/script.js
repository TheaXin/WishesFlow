const screens = Object.fromEntries(['start', 'checkin', 'unlock', 'done'].map((name) => [name, document.querySelector(`#screen-${name}`)]));
const steps = document.querySelectorAll('[data-step]');
function show(name, step) {
  Object.values(screens).forEach((screen) => screen.classList.add('is-hidden'));
  screens[name].classList.remove('is-hidden');
  steps.forEach((item) => item.classList.toggle('is-active', Number(item.dataset.step) <= step));
}
document.querySelector('#start-demo').addEventListener('click', () => show('checkin', 2));
document.querySelector('#checkin-demo').addEventListener('click', () => show('unlock', 3));
document.querySelector('#unlock-demo').addEventListener('click', () => show('done', 3));
document.querySelector('#reset-demo').addEventListener('click', () => show('start', 1));
