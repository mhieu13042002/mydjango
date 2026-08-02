/**
 * Định dạng số tiền kiểu Việt Nam: 100.000 (dấu chấm ngăn hàng nghìn).
 * Cách dùng: thêm class="js-money-input" vào bất kỳ <input> nhập số tiền nào.
 * Giá trị thật (không dấu chấm) được đồng bộ vào input ẩn cùng name,
 * hoặc bạn có thể đọc qua thuộc tính data-raw-value khi submit.
 *
 * <input type="text" class="js-money-input" name="amount" inputmode="numeric" placeholder="0">
 */
(function () {
  function formatVND(rawDigits) {
    if (!rawDigits) return "";
    return rawDigits.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  }

  function attach(input) {
    // Nếu đã có giá trị sẵn (VD khi load trang edit), format ngay
    if (input.value) {
      const digits = input.value.replace(/\D/g, "");
      input.value = formatVND(digits);
      input.dataset.rawValue = digits;
    }

    input.addEventListener("input", function (e) {
      const cursorFromEnd = input.value.length - input.selectionStart;
      const digits = input.value.replace(/\D/g, "").slice(0, 15); // chặn số quá dài
      const formatted = formatVND(digits);

      input.value = formatted;
      input.dataset.rawValue = digits;

      // Giữ vị trí con trỏ hợp lý sau khi thêm dấu chấm
      const newPos = Math.max(formatted.length - cursorFromEnd, 0);
      input.setSelectionRange(newPos, newPos);
    });

    // Trước khi submit form, gỡ dấu chấm để backend nhận số nguyên sạch
    const form = input.closest("form");
    if (form) {
      form.addEventListener("submit", function () {
        input.value = input.dataset.rawValue || input.value.replace(/\D/g, "");
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".js-money-input").forEach(attach);
  });

  // Hàm tiện ích dùng để hiển thị số tiền tĩnh (VD trong dashboard, lịch sử)
  window.formatMoney = function (num) {
    return formatVND(String(Math.round(Number(num) || 0)));
  };
})();
