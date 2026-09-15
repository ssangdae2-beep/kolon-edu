const test = require("node:test");
const assert = require("node:assert");
const noteService = require("../src/services/noteService");

test("createNote는 제목과 내용을 가진 노트를 생성한다", () => {
  const note = noteService.createNote("첫 메모", "내용입니다");
  assert.strictEqual(note.title, "첫 메모");
  assert.ok(note.id);
});

// 실습 07(10장)에서 아래와 같은 테스트를 Bob과 함께 추가합니다:
// - 빈 제목으로 생성 시도 시 실패해야 하는 테스트 (현재 버그 재현용)
// - content 없이 생성 시 빈 문자열로 저장되는지 확인하는 테스트
// - 존재하지 않는 id 조회/삭제 시 처리 확인하는 테스트
