// 메모리 저장소 (실습용 — 재시작하면 초기화됨)
let notes = [];
let nextId = 1;

function getAllNotes() {
  return notes;
}

function getNoteById(id) {
  return notes.find((n) => n.id === Number(id));
}

// TODO(실습 07): title이 빈 문자열이거나 공백뿐이어도 그대로 저장되는 버그가 있습니다.
// 10장 실습에서 Bob과 함께 이 버그를 재현하고 고칩니다.
function createNote(title, content) {
  const note = {
    id: nextId++,
    title: title,
    content: content || "",
    createdAt: new Date().toISOString(),
  };
  notes.push(note);
  return note;
}

function deleteNote(id) {
  const before = notes.length;
  notes = notes.filter((n) => n.id !== Number(id));
  return notes.length < before;
}

module.exports = { getAllNotes, getNoteById, createNote, deleteNote };
